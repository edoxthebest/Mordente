git clone git@github.com:edoxthebest/SELinuxTool.git
# vscode make .venv environment
pip install -e .
# Assuming we have libmata built
## Issue with version -- need libmata 1.16.3 or higher
## git clone https://github.com/VeriFIT/mata
## make -C bindings/python install          # forse non necessario
## make -C bindings/python build-dist
pip install bindings/python/dist/libmata-1.20.0.tar.gz
git clone https://github.com/SELinuxProject/setools.git
git checkout 4.5.1 # do we need anything else?
git clone git@github.com:SELinuxProject/selinux.git
git checkout 3.8.1
make clean distclean
make install #this fails
SEPOL_SRC=selinux/libsepol/ python setup.py build_ext -i
pip install setools/  # non pip install setools (ma quello che abbiamo appena buildato)
