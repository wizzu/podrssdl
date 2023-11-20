

venv:
	python3 -m venv venv
	./venv/bin/pip3 install --upgrade pip

installdeps:
	./venv/bin/pip3 install -r requirements.txt
