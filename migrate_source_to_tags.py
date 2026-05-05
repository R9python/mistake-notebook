#!/usr/bin/env python3
"""
数据迁移脚本：将 Mistake.source 字段迁移到标签系统

功能：
1. 提取所有唯一的 source 值
2. 为每个 source 创建对应的 Tag
3. 建立 Mistake 和 Tag 的多对多关联
4. 保留原 source 字段作为备份（不删除）
"""

from app import app
from models import db, Mistake, Tag, MistakeTag
from sqlalchemy import text

def migrate():
    with app.app_context():
        print("开始数据迁移：source → tags")
        print("=" * 50)

        # 1. 获取所有唯一的 source 值
        sources = db.session.query(Mistake.source).distinct().all()
        source_values = [s[0] for s in sources if s[0]]  # 过滤掉 None 和空字符串

        print(f"\n发现 {len(source_values)} 个唯一的来源值：")
        for src in source_values:
            print(f"  - {src}")

        if not source_values:
            print("\n没有需要迁移的数据。")
            return

        # 2. 为每个 source 创建 Tag（如果不存在）
        print("\n创建标签...")
        tag_map = {}  # source -> Tag 对象
        colors = ['#0078D4', '#107C10', '#D83B01', '#5C2D91', '#008272', '#CA5010']

        for idx, source_value in enumerate(source_values):
            # 检查标签是否已存在
            existing_tag = Tag.query.filter_by(name=source_value).first()
            if existing_tag:
                tag_map[source_value] = existing_tag
                print(f"  标签已存在: {source_value}")
            else:
                # 创建新标签，循环使用颜色
                new_tag = Tag(
                    name=source_value,
                    color=colors[idx % len(colors)]
                )
                db.session.add(new_tag)
                tag_map[source_value] = new_tag
                print(f"  创建标签: {source_value} (颜色: {colors[idx % len(colors)]})")

        db.session.commit()
        print(f"\n标签创建完成，共 {len(tag_map)} 个。")

        # 3. 建立 Mistake 和 Tag 的关联
        print("\n建立错题-标签关联...")
        mistakes = Mistake.query.filter(Mistake.source.isnot(None), Mistake.source != '').all()

        migrated_count = 0
        skipped_count = 0

        for mistake in mistakes:
            if mistake.source in tag_map:
                tag = tag_map[mistake.source]

                # 检查关联是否已存在
                existing = MistakeTag.query.filter_by(
                    mistake_id=mistake.id,
                    tag_id=tag.id
                ).first()

                if not existing:
                    # 创建关联
                    mistake.tags.append(tag)
                    migrated_count += 1
                else:
                    skipped_count += 1

        db.session.commit()

        print(f"\n关联建立完成：")
        print(f"  - 新建关联: {migrated_count} 条")
        print(f"  - 跳过已存在: {skipped_count} 条")

        # 4. 统计信息
        print("\n" + "=" * 50)
        print("迁移完成！统计信息：")
        print(f"  - 总标签数: {Tag.query.count()}")
        print(f"  - 总错题数: {Mistake.query.count()}")
        print(f"  - 有标签的错题: {db.session.query(Mistake).join(Mistake.tags).distinct().count()}")
        print(f"  - 无标签的错题: {Mistake.query.filter(~Mistake.tags.any()).count()}")

        print("\n注意：原 source 字段已保留作为备份，如需清空请手动操作。")
        print("=" * 50)

if __name__ == '__main__':
    try:
        migrate()
    except Exception as e:
        print(f"\n迁移失败: {e}")
        import traceback
        traceback.print_exc()
