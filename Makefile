# This needs to be updated to pyproject.toml and poetry

AWS_PROFILE=fas
AWS_REGION=us-east-2
export AWS_PROFILE
export AWS_REGION

DOMAIN=cybersecurity-policy.org
STACK=iga236-home
CODE_DIR=iga_236
REQUIREMENTS=iga_236/requirements.txt


.PHONY: build deploy clean install lint check test
clean:
	@echo "--- Cleaning old build artifacts ---"
	rm -rf .aws-sam

$(REQUIREMENTS): poetry.lock pyproject.toml
	@echo "--- Exporting requirements.txt from Poetry ---"
	poetry export -f requirements.txt --output $(REQUIREMENTS) --without-hashes

install:
	poetry install --with dev

build: clean template.yaml samconfig.toml
	printenv | grep AWS
	(cd lab1_crypto  &&  make lint && make build)
	(cd lab1_guesser &&  make lint && make build)
	make lint
	make check
	sam validate --lint
	sam build --use-container --parallel

deploy:
	make build
	sam deploy --stack-name $(STACK) \
		--parameter-overrides \
			DeploymentTimestamp="$$(date +'%Y-%m-%dT%H:%M:%S%z %Z')" \
			EnvironmentName="prod" \
			HostedZoneId="Z067345623G6IQ9M53QSI" \
			LogLevel="DEBUG" \
		--no-confirm-changeset
	curl --silent  https://$(DOMAIN)/ | head -3

check: install
	printenv | grep AWS
	poetry run pytest $(CODE_DIR) --log-cli-level=DEBUG

lint: install
	poetry run pylint iga_236
	poetry run pyright iga_236

# https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-sam-cli-sync.html
sync:
	sam sync --watch --stack-name iga236-home

tail:
	sam logs --stack-name $(STACK) --tail  --region us-east-2  --profile fas

# Useful functions
list-cloud-resources:
	printenv | grep AWS
	aws cloudformation list-stack-resources \
	  --stack-name $(STACK) \
	  --query "StackResourceSummaries[?ResourceType=='AWS::ApiGatewayV2::DomainName'].[LogicalResourceId,PhysicalResourceId,ResourceStatus]" \
	  --output table

wipe-the-stack:
	aws cloudformation delete-stack --stack-name $(STACK)
	aws cloudformation wait stack-delete-complete --stack-name $(STACK) --region us-east-2


distclean:
	/bin/rm -rf .venv
	/bin/rm -f instance/message_board.db

################################################################
## this is in Makefile.dev

create-tables:
	for fn in etc/dynamodb_*.json ; do aws dynamodb create-table --cli-input-json file://$$fn ; done
	aws dynamodb list-tables --output text

delete-tables:
	for fn in etc/dynamodb_*.json ; do aws dynamodb delete-table --table-name $$(echo $$fn | sed s:etc/dynamodb_:: | sed s:.json::) ; done
	aws dynamodb list-tables --output text

scan-tables:
	for fn in etc/dynamodb_*.json ; do aws dynamodb scan --table-name $$(echo $$fn | sed s:etc/dynamodb_:: | sed s:.json::) ; done
	aws dynamodb list-tables --output text

list-tables:
	aws dynamodb list-tables
