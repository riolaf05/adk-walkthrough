# pip install google-adk

import asyncio
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from dotenv import load_dotenv
load_dotenv(override=True) # Load environment variables from .env file
import os
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY')

async def get_tools_async():
    """Gets tools from the Math MCP Server."""
    print("Attempting to connect to MCP Math server...")
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
        command='python',  
        args=["-m", "mcp_server_calculator"],
          )
        )
    print("MCP Toolset created successfully.")
    return tools, exit_stack

async def get_agent_async():
    """Creates an ADK Agent equipped with tools from the MCP Server."""
    tools, exit_stack = await get_tools_async()
    print(f"Fetched {len(tools)} tools from MCP server.")
    root_agent = LlmAgent(
        model='gemini-2.0-flash',
        name='Math_assistant',
        instruction='Help user with Math operations.',
        tools=tools, 
    )
    return root_agent, exit_stack

async def async_main(query: str):
    session_service = InMemorySessionService()
    session = session_service.create_session(
       state={}, app_name='Math_assistant', user_id='user_fs'
    )
    content = types.Content(role='user', parts=[types.Part(text=query)])
    root_agent, exit_stack = await get_agent_async()
    runner = Runner(
        app_name='Math_assistant',
        agent=root_agent,
        session_service=session_service,
    )
    print("Running agent...")
    events_async = runner.run_async(
        session_id=session.id, user_id=session.user_id, new_message=content
    )
    async for event in events_async:
        print(f"Event received: {event.content}")

        if event.is_final_response():
            print(f"Final response: {event.content}")
            print(f"Final response parts: {event.content.parts}")
            print(f"Final response text: {event.content.parts[0].text}")
            break

    print("Closing MCP server connection...")
    await exit_stack.aclose()
    print("Cleanup complete.")

if __name__ == '__main__':
   input_query = "How much is 475 * 23?"
   asyncio.run(async_main(input_query))