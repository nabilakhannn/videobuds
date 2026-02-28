.PHONY: setup run reset-db clean

setup:
	pip3 install -r app_requirements.txt
	pip3 install -r tools/requirements.txt
	@echo "Setup complete. Run 'make run' to start."

run:
	python3 run.py

reset-db:
	rm -f /tmp/scalebuds.db
	@echo "Database reset. Run 'make run' to recreate."

clean:
	rm -f /tmp/scalebuds.db
	rm -rf app/static/generated/*
	rm -rf app/static/uploads/*
	@echo "Cleaned database and generated files."
