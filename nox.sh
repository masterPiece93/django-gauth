echo "Loding Test Env ..."
set -a
source tests/.env.test
set +a
echo -e "Loaded .test.env !\n"
echo "Nox ..."
nox@djangoGauth-offc "$@" # must be the nox command that is Installed ( if via Pipx )
