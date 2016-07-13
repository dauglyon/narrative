"""
Updates Narratives to the most recent version.
This is intended to operate on the Narrative Typed Object as returned
from the Workspace, BEFORE it gets transformed into a notebook model.
(e.g. should be injected into narrativeio.KBaseWSManagerMixin.read_narrative
 when content==True)

It should be noted here that if an update occurs, job ids will no longer be available.
"""
import uuid
import json
import re
import datetime
import biokbase.narrative.clients as clients

def update_needed(narrative):
    # simple enough - if there's a "kbase" block
    # in the metadata, it's been updated.
    return 'kbase' not in narrative['metadata']

def update_narrative(narrative):
    """
    Updates the Narrative to the most recent version.
    If no updates are necessary, just returns the narrative.
    """
    if not update_needed(narrative):
        return narrative

    updated_cells = list()

    if 'worksheets' in narrative:
        cells = narrative['worksheets'][0]['cells']
    else:
        cells = narrative['cells']

    for idx, cell in enumerate(cells):
        updated_cells.append(update_cell(cell))
        # cell = update_cell(cell)
        # if cell.get('metadata', {}).get('kbase', {}).get('updated', False):
        #     updated_cells.add(idx)

    updated_metadata = update_metadata(narrative['metadata'])
    if 'worksheets' in narrative:
        narrative['worksheets'][0] = {
            'cells': updated_cells,
            'metadata': updated_metadata
        }
    else:
        narrative['cells'] = updated_cells
        narrative['metadata'] = updated_metadata
    return narrative

def update_cell(cell):
    """
    Look for what kind of cell it is.
    if code cell, do nothing.
    if Markdown cell, and it has kb-cell in its metadata, do something.
    if kb-cell.type == kb_app, go to update_app_cell
    if kb-cell.type == function_input , go to update_method_cell
    if kb-cell.type == function_output , go to update_output_cell
    """
    if cell.get('cell_type', None) != 'markdown':
        return cell
    meta = cell['metadata']

    kb_cell_type = meta.get('kb-cell', {}).get('type', None)
    if kb_cell_type == 'kb_app':
        cell = update_app_cell(cell)
    elif kb_cell_type == 'function_input':
        cell = update_method_cell(cell)
    elif kb_cell_type == 'function_output':
        cell = update_output_cell(cell)

    return cell

def update_method_cell(cell):
    """
    Updates a single method cell to fill these two constraints:
    1. Become a code cell, NOT a markdown cell.
    2. Translate the cell's metadata to the right structure.
    3. Remove the MD code from the source area.

    Some assumptions made here:
    1. Jobs associated with the cell are not available. So the only
       states are either editing or complete (default to editing)
    2. We don't know what tag the methods came from, so go with 'release'
    """
    # 1. Get its metadata and update it to be new cell-ish
    meta = cell['metadata']['kb-cell']
    if 'method' not in meta:
        # throw an error?
        return cell

    # try to find cell_id, if not, make up a new one.

    method_info = meta['method'].get('info', {})
    method_behavior = meta['method'].get('behavior', {})
    widget_state = meta.get('widget_state', [])
    if len(widget_state):
        widget_state = widget_state[0]
    else:
        widget_state = {}

    runtime_state = None
    if 'state' in widget_state:
        runtime_state = widget_state['state']

    method_params = runtime_state.get('params', None)
    if not method_params:
        method_params = {}

    # guess at the FSM state for the method cell from the runtime_state.runningState
    cur_state = runtime_state.get('runningState', 'input')
    fsm_state = {}
    if cur_state == 'input':
        fsm_state = {
            'mode': 'editing',
            'params': 'incomplete'
        }
    elif cur_state in ['submitted', 'queued', 'running', 'error']:
        # no longer access to the job, so just reset to input
        fsm_state = {
            'mode': 'editing',
            'params': 'complete'
        }
    else:
        # only one left is complete...
        fsm_state = {
            'mode': 'success',
            'params': 'complete'
        }

    ts = widget_state.get('time', None)
    if ts:
        ts = datetime.datetime.utcfromtimestamp(ts/1000.0).strftime('%a, %d %b %Y %H:%M:%S GMT')

    git_hash = method_info.get('git_commit_hash', None)
    app_name = method_info.get('id', '')
    # the app_name in this case, is everything after the slash. So MegaHit/run_megahit would just be 'run_megahit'
    app_name = app_name[app_name.find('/')+1:]
    module_name = method_behavior.get('kb_service_name', None)
    tag = None
    # now we get the version, if it exists.
    print("{}/{}".format(module_name, git_hash))
    # Suddenly, this is very complex...
    # Need git_hash and module_name to look up the version.
    # if lookup succeeds -
    #   if has a release tag, use it.
    #   if not, lookup the module's info (get_module_info), use the most released one (release > beta > dev) and change the hash
    # if lookup fails -
    #   try again with just the module info
    #   if THAT fails, the cell can't be updated.
    # if no git_hash or module_name, it's not an SDK-based cell and can't be looked up.
    if git_hash and module_name:
        cat = clients.get('catalog')
        tag_pref_order = ['release', 'beta', 'dev']
        try:
            print('looking up ' + module_name + ' hash ' + git_hash)
            version_info = cat.get_module_version({'module_name': module_name, 'version': git_hash})
            if 'release_tags' in version_info:
                tags = version_info['release_tags']
                if len(tags) > 0:
                    tags = [t.lower() for t in tags]
                    for tag_pref in tag_pref_order:
                        if tag_pref in tags:
                            tag = tag_pref
                if tag is None:
                    raise Exception("No release tag found!")
        except Exception as e:
            print("Exception found: {}".format(str(e)))
            try:
                print("Searching for module info...")
                mod_info = cat.get_module_info({'module_name': module_name})
                # look for most recent (R > B > D) release tag with the app.
                for tag_pref in tag_pref_order:
                    tag_info = mod_info.get(tag_pref, None)
                    if tag_info is not None and app_name in tag_info.get('narrative_methods', []):
                        tag = tag_pref
                        break
                print("tag set to {}".format(tag))
            except Exception as e2:
                print("Exception found: {}".format(e2))
    else:
        # it's not an SDK method! do something else!
        return obsolete_method_cell(cell, method_info.get('name'), method_params)

    new_meta = {
        'type': 'app',
        'attributes': {
            'title': method_info.get('name', 'Unnamed App'),
            'id': unicode(uuid.uuid4()),
            'status': 'new',
            'created': ts,          # default to last saved time
            'lastLoaded': ts,
        },
        'appCell': {
            'app': {
                'id': method_info.get('id', 'unknown'),
                'gitCommitHash': git_hash,
                'version': method_info.get('ver', None),
                'tag': tag
            },
            'state': {
                'edit': 'editing',
                'params': None,
                'code': None,
                'request': None,
                'result': None
            },
            'params': method_params,
            'user-settings': {
                'showCodeInputArea': False,
                'showDeveloperOptions': False
            }
            # 'fsm': {
            #     'currentState': fsm_state
            # }
        }
    }

    # Finally, turn it into a code cell.
    cell['cell_type'] = u'code'
    cell['execution_count'] = None
    cell['outputs'] = []
    cell['metadata']['kbase'] = new_meta
    del cell['metadata']['kb-cell']
    cell['source'] = u''
    return cell

def obsolete_method_cell(cell, app_name, params):
    cell['cell_type'] = 'markdown'
    format_params = '<ul>' + '\n'.join(['<li>{} - {}</li>'.format(p, params[p]) for p in params]) + '</ul>'
    base_source = """<div style="border:1px solid #CECECE; padding: 5px">
    <div style="font-size: 120%; font-family: 'OxygenBold', Arial, sans-serif; color:#2e618d;">Obsolete App!</div>
    <div style="font-family: 'OxygenBold', Arial, sans-serif;">
    {}
    </div>
    Sorry, this app is obsolete and can no longer function. But don't worry! Any outputs of this method have been retained.
    <br>Parameters:
    {}
    </div>"""

    cell['source'] = unicode(base_source.format(app_name, format_params))

    # cell['source'] = unicode('\n'.join([
    #     "### Obsolete Cell!",
    #     "Sorry, this cell\'s app is obsolete. Any outputs of this method have been retained.  ",
    #     "**" + app_name + "**  ",
    #     "Parameters:  ",
    #     format_params
    # ]))
    del cell['metadata']['kb-cell']
    return cell

def update_app_cell(cell):
    """
    Updates an app cell to the new style (which is deprecated...)
    """
    meta = cell['metadata']['kb-cell']
    app_name = meta.get('app', {}).get('info', {}).get('name', 'Unknown app') + " (multi-step app)"
    cell = obsolete_method_cell(cell, app_name, {})
    cell['metadata']['kbase'] = {'old_app': True, 'info': meta}
    return cell

def update_output_cell(cell):
    """
    Updates an output viewer cell to the right new format.
    """
    # hoo-boy, here's the hard one.
    # Grab the source, parse it, build a new viewer for it,
    # put that in a code cell, and execute it.
    # ... maybe directly change the output area? Might be easier ...
    return cell

def update_metadata(metadata):
    """
    Updates the narrative (e.g. notebook) metadata to the new format.
    """
    if 'kbase' in metadata:
        return metadata
    else:
        metadata['kbase'] = {
            'job_ids': metadata.get('job_ids', {}),
            'name': metadata.get('name', ''),
            'creator': metadata.get('creator', ''),
            'ws_name': metadata.get('ws_name', '')
        }
        # delete the old here, but we'll do that later once the rest
        # of the system supports that.
    return metadata