from backend.service.text_generate_ai import rewrite_paragraph
if __name__ == "__main__":
    original_paragraph = "Công nghệ AI đã có sự phát triển vượt bậc trong những năm gần đây. Nó đang được áp dụng trong nhiều lĩnh vực như chăm sóc sức khỏe, tài chính và giáo dục."

    rewritten_paragraph = rewrite_paragraph(original_paragraph)
    print("Đoạn văn gốc: \n", original_paragraph)
    print("\nĐoạn văn đã viết lại: \n", rewritten_paragraph)
