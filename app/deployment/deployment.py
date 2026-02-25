#
# import logging
# import os
#
# from dotenv import load_dotenv, set_key
# from vertexai import agent_engines
# from vertexai.preview.reasoning_engines import AdkApp
#
# from agent import root_agent
# load_dotenv()
#
# ENV_FILE_PATH = os.path.abspath(
#     os.path.join(os.path.dirname(__file__), "..", ".env")
# )
#
# # Function to update the .env file
# def update_env_file(agent_engine_id, env_file_path):
#     """Updates the .env file with the tools engine ID."""
#     try:
#         set_key(env_file_path, "AGENT_ENGINE_ID", agent_engine_id)
#         print(
#             f"Updated AGENT_ENGINE_ID in {env_file_path} to {agent_engine_id}"
#         )
#     except Exception as e:
#         print(f"Error updating .env file: {e}")
#
#
#
# app = AdkApp(
#     agent=root_agent,
#     enable_tracing=True,
# )
#
# logging.debug("deploying tools to tools engine:")
#
# remote_app = agent_engines.create(
#     app,
#     display_name="city_library_agent",
#     requirements=[
#         "google-cloud-aiplatform[adk,tools-engines]>=1.100.0,<2.0.0",
#         "google-adk>=1.5.0,<2.0.0",
#         "python-dotenv",
#         "google-cloud-secret-manager",
#     ],
#     extra_packages=[
#         "./app",
#     ],
# )
