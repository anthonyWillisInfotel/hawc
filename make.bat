@ECHO off

if "%~1" == "" goto :help
if /I %1 == help goto :help
if /I %1 == sync-dev goto :sync-dev
if /I %1 == build goto :build
if /I %1 == build-pex goto :build-pex
if /I %1 == lint goto :lint
if /I %1 == format goto :format
if /I %1 == lint-py goto :lint-py
if /I %1 == format-py goto :format-py
if /I %1 == lint-js goto :lint-js
if /I %1 == format-js goto :format-js
if /I %1 == test goto :test
if /I %1 == test-integration goto :test-integration
if /I %1 == test-refresh goto :test-refresh
if /I %1 == test-js goto :test-js
if /I %1 == coverage goto :coverage
if /I %1 == loc goto :loc
goto :help

:help
echo.Please use `make ^<target^>` where ^<target^> is one of
echo.  sync-dev          sync dev environment after code checkout
echo.  build             build python wheel
echo.  build-pex         build pex bundle (mac/linux only)
echo.  test              run python tests
echo.  test-integration  run integration tests (requires npm run start)
echo.  test-refresh      removes mock requests and runs python tests
echo.  test-js           run javascript tests
echo.  coverage          run coverage and create html report
echo.  lint              perform both lint-py and lint-js
echo.  format            perform both format-py and lint-js
echo.  lint-py           check for pytho formatting issues via black and flake8
echo.  format-py         modify python code using black and show flake8 issues
echo.  lint-js           check for javascript formatting issues
echo.  format-js         modify javascript code if possible using linters and formatters
echo.  loc               generate lines of code report
goto :eof

:sync-dev
python -m pip install -U pip
pip install -r requirements/dev.txt
yarn --cwd frontend
manage.py migrate
goto :eof

:build
del /f /q .\build .\dist
call npm --prefix .\frontend run build
manage.py set_git_commit
python setup.py bdist_wheel
goto :eof

:build-pex
echo.Pex is not compatibile with windows; linux or mac is required.
goto :eof

:lint
black . --check && flake8 .
npm --prefix .\frontend run lint
goto :eof

:format
black . && isort . && flake8 .
npm --prefix .\frontend run format
goto :eof

:lint-py
black . --check && flake8 .
goto :eof

:format-py
black . && isort . && flake8 .
goto :eof

:lint-js
npm --prefix .\frontend run lint
goto :eof

:format-js
npm --prefix .\frontend run format
goto :eof

:test
py.test
goto :eof

:test-integration
HAWC_INTEGRATION_TESTS=1 SHOW_BROWSER=1 BROWSER="firefox" py.test -s tests/frontend/integration/
goto :eof

:test-refresh
rmdir /s /q .\tests\data\cassettes
py.test
goto :eof

:test-js
npm --prefix .\frontend run test-windows
goto :eof

:coverage
coverage run -m pytest
coverage html -d coverage_html
echo "Report ready; open ./coverage_html/index.html to view"
goto :eof

:loc
cloc --exclude-dir=migrations,node_modules,public,private,vendor,venv --exclude-ext=json,yaml,svg,toml,ini --vcs=git --counted loc-files.txt .
goto :eof
