import re

# Your input paragraph
paragraph = """
1. Thử thách Nhân vật Bí Ẩn Mới đã trở lại!
Tập 2
Chào các Chỉ huy! Một nhân vật mới đã xuất hiện trong cộng đồng! Lần trước, chúng tôi đã đánh giá thấp kiến thức Red Alert của bạn, nên lần này độ khó đã được tăng lên. Liệu bạn có thể dựa vào manh mối để đoán ra đây là ai không?

2. Thách Đố Nhân Vật Bí Ẩn - Đã Quay Trở Lại!
Phần 2
Xin chào các Chỉ huy! Một nhân vật mới đã gia nhập cộng đồng! Lần trước, chúng tôi đã coi thường hiểu biết Red Alert của bạn, nên lần này độ khó đã được đẩy lên cao hơn. Bạn có đủ khả năng giải mã manh mối để đoán ra danh tính nhân vật này?
3. Thử Thách Nhân Vật Bí Ẩn Mới Đã Tới!
Tập 2
Chào các Chỉ Huy! Một nhân vật mới đã xuất hiện trong cộng đồng! Lần trước, chúng tôi đã đánh giá thấp kiến thức Red Alert của bạn, nên lần này độ khó đã được tăng lên. Bạn có thể dựa vào manh mối để đoán ra nhân vật này không?

4. Sự Kiện Nhân Vật Bí Ẩn - Đã Quay Trở Lại!
Tập 2
Xin chào các Chỉ Huy! Một nhân vật mới đã gia nhập cộng đồng! Lần trước, chúng tôi đã coi thường hiểu biết Red Alert của bạn, nên lần này thử thách sẽ khó hơn. Liệu bạn có thể giải mã manh mối để nhận diện nhân vật này?
5. Thử Thách Nhân Vật Bí Ẩn Mới Đã Tới!
Tập 2
Chào các Chỉ Huy! Một nhân vật mới đã xuất hiện trong cộng đồng! Lần trước, chúng tôi đã đánh giá thấp kiến thức Red Alert của bạn, nên lần này độ khó đã được tăng lên. Liệu bạn có thể dựa vào manh mối để đoán ra danh tính nhân vật?

6. [THỬ THÁCH MỚI] Nhân Vật Bí Ẩn - Tập 2
Xin chào các Chỉ Huy! Một nhân vật mới đã gia nhập cộng đồng! Sau lần trước đánh giá thấp hiểu biết Red Alert của bạn, lần này chúng tôi tăng độ khó. Bạn có đủ khả năng giải mã manh mối để nhận diện nhân vật?
7. Thử Thách Nhân Vật Bí Ẩn Mới Đã Tới!
Tập 2
Chào các Chỉ Huy! Một nhân vật mới đã xuất hiện trong cộng đồng! Lần trước, chúng tôi đã đánh giá thấp hiểu biết của bạn về Red Alert, nên lần này độ khó đã được tăng lên. Bạn có thể dựa vào manh mối để đoán ra nhân vật này không?

8. Thách Đố Nhân Vật Bí Ẩn - Đã Quay Trở Lại!
Tập 2
Xin chào các Chỉ Huy! Một nhân vật mới đã gia nhập cộng đồng! Lần trước, chúng tôi đã xem nhẹ kiến thức Red Alert của bạn, nên lần này độ khó đã được nâng cấp. Liệu bạn có thể giải mã danh tính nhân vật này từ những gợi ý?
9. Thử Thách Nhân Vật Bí Ẩn Mới Đã Tới!
Tập 2
Chào các Chỉ Huy! Một nhân vật mới đã xuất hiện trong cộng đồng! Lần trước, chúng tôi đã đánh giá thấp kiến thức Red Alert của bạn, nên lần này độ khó đã được tăng lên. Bạn có thể dựa vào manh mối để đoán ra ai không?

10. Sự Kiện Nhân Vật Bí Ẩn Mới Đã Mở!
Tập 2
Xin chào các Chỉ Huy! Một nhân vật mới đã góp mặt trong cộng đồng! Lần trước chúng tôi đã coi thường hiểu biết Red Alert của bạn, nên lần này độ khó đã được nâng cấp. Liệu bạn có thể dùng gợi ý để đoán ra danh tính nhân vật?
"""

# Regular expression to match the text between the numbers and remove the numbers
pattern = r'(\d+\..*?)(?=\n\d+\.|\Z)'

# Find all matches and remove the number at the start of each match
matches = re.findall(pattern, paragraph, re.DOTALL)

# Remove the "1.", "2.", etc., and print the result
for idx, match in enumerate(matches, 1):
    # Remove the number and the dot at the start of each section
    cleaned_text = re.sub(r'^\d+\.\s*', '', match.strip())
    print(f"----------------- {idx} ---------------")
    print(f"{cleaned_text}\n")