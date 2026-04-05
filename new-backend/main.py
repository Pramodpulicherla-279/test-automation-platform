from fastapi import FastAPI
from modules.test_runner.routes import router as test_router
# from modules.jira.routes import router as jira_router
# from modules.slack.routes import router as slack_router

app = FastAPI()

app.include_router(test_router, prefix="/test")
# app.include_router(jira_router, prefix="/jira")
# app.include_router(slack_router, prefix="/slack")