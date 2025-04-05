from backend.service.text_generate_ai import rewrite_paragraph

if __name__ == "__main__":
    rewritten_paragraph = rewrite_paragraph()
    print("\nĐoạn văn đã viết lại: \n", rewritten_paragraph)
