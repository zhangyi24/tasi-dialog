import logging

def qa_kb_stat(user_utter, global_vars, context):
    if context["builtin_vars"]["response_src"] == "kb":
        qa_kb_retrieve_result = context["builtin_vars"]["qa_kb_result"]
        logging.info(f"qa_kb_retrieve_result: {qa_kb_retrieve_result}")