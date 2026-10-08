# import os
# from unittest.mock import MagicMock
# from dotenv import load_dotenv
# load_dotenv()

# # Import from your module (adjust import path if needed)
# from hr_agent.agent.graph import GraphDeps, compile_graph, save_graph_image


# def generate_and_save_graph(output_path: str = "hr_agent_graph.png") -> str:
#     """Initializes dummy dependencies, compiles the graph, and saves the image."""
    
#     # Use MagicMock so you don't need real API keys or initialized models to build/draw the graph
#     mock_runnable = MagicMock()

#     deps = GraphDeps(
#         scope_llm=mock_runnable,
#         router_llm=mock_runnable,
#         kb_grader_llm=mock_runnable,
#         web_grader_llm=mock_runnable,
#         groundness_llm=mock_runnable,
#         rewriter_llm=mock_runnable,
#         generator_llm=mock_runnable,
#         memory_extractor_llm=mock_runnable,
#         summarizer_llm=mock_runnable,
#         retriever=mock_runnable,
#         contextualize_llm=mock_runnable,
#         web_search=mock_runnable,
#     )

#     # Compile graph schema
#     compiled_graph = compile_graph(deps)

#     # Save to file
#     save_graph_image(compiled_graph, output_path)
    
#     abs_path = os.path.abspath(output_path)
#     print(f"Graph image saved successfully to: {abs_path}")
#     return abs_path


# def view_graph_image(file_path: str) -> None:
#     """Attempts to automatically open the generated image in the default system viewer."""
#     try:
#         from PIL import Image
#         img = Image.open(file_path)
#         img.show()
#     except Exception as e:
#         print(f"Could not automatically open image: {e}")


# if __name__ == "__main__":
#     target_path = "images/hr_agent_graph.png"
    
#     # 1. Generate and save the PNG
#     saved_file = generate_and_save_graph(target_path)
    
#     # 2. Display the saved image
#     view_graph_image(saved_file)


from hr_agent.agent.runner import ask_agent

result = ask_agent(
    question = "What are the duties and obligations of GESCI?",
    user_id = "tipto",
    chat_id = "test_chat_001",
    verbose = True
)

print("\nFinal Result:\n", result)