dir=$(pwd)
narrdir=$(cd ..;pwd)

export NARRATIVE_DIR=$narrdir
export JUPYTER_CONFIG_DIR=$narrdir/kbase-extension
export JUPYTER_RUNTIME_DIR=/tmp/jupyter_runtime
export JUPYTER_DATA_DIR=/tmp/jupyter_data
export JUPYTER_PATH=$narrdir/kbase-extension
export IPYTHONDIR=$narrdir/kbase-extension/ipython

echo 'Root dir'
echo ${dir}

jupyter nbextension install ${dir}/methodCell --symlink --sys-prefix
jupyter nbextension enable methodCell/main --sys-prefix