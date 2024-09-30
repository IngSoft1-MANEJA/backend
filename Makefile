run-tests_crud:
	ENVIRONMENT=test PYTHONPATH=$(shell pwd) pytest -k "crud" -vv
	rm -f database_test.sqlite
	unset ENVIRONMENT

run-test_endpoints: # Run all tests ENDPOINTS to Database
	ENVIRONMENT=test python tests/populate_test_db.py
	pytest -m endpoints -vv
	rm database_test.sqlite
	unset ENVIRONMENT
