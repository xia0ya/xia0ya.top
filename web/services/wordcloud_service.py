# -*- coding: utf-8 -*-
"""词云生成模块"""

import json
import logging
from collections import Counter
from pathlib import Path

import jieba
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# 停用词文件
STOP_WORDS_FILE = Path(__file__).parent.parent / "docs" / "hit_stopwords.txt"

# 中文字体（使用系统自带微软雅黑）
FONT_PATHS = [
    "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",  # 黑体
    "/System/Library/Fonts/PingFang.ttc",  # Mac 苹方
    "/System/Library/Fonts/STHeiti Light.ttc",  # Mac 黑体
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux Noto Sans CJK
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",  # Linux Noto Serif CJK
]

def get_font_path():
    """获取可用的中文字体路径"""
    for path in FONT_PATHS:
        if Path(path).exists():
            return path
    return None

class WordCloudGenerator:
    def __init__(self):
        logging.getLogger('jieba').setLevel(logging.WARNING)
        self.stop_words = self._load_stop_words()
        self.font_path = get_font_path()

    def _load_stop_words(self):
        """加载停用词"""
        try:
            with open(STOP_WORDS_FILE, 'r', encoding='utf-8') as f:
                return set(f.read().split('\n'))
        except Exception:
            return set()

    def generate(self, reviews, save_dir=None):
        """
        从评论生成词云

        Args:
            reviews: 评论列表，每个评论是包含 'content' 字段的对象
            save_dir: 保存目录，默认使用项目根目录
        """
        if not reviews:
            return None, None

        if not self.font_path:
            logging.warning("未找到中文字体，跳过词云生成")
            return None, None

        # 合并所有评论内容
        all_text = ' '.join(r.content for r in reviews if hasattr(r, 'content') and r.content)
        if not all_text.strip():
            return None, None

        # 分词
        words = [word for word in jieba.lcut(all_text)
                 if word not in self.stop_words
                 and len(word.strip()) > 1
                 and word.isalpha()]

        # 词频统计
        word_freq = Counter(words)

        # 保存词频文件
        freq_file = None
        if save_dir:
            freq_path = Path(save_dir) / "word_frequency.json"
            freq_path.parent.mkdir(parents=True, exist_ok=True)
            with open(freq_path, 'w', encoding='utf-8') as f:
                json.dump(dict(word_freq.most_common(50)), f, ensure_ascii=False, indent=2)
            freq_file = str(freq_path)

        # 生成词云
        try:
            top_words = dict(word_freq.most_common(30))
            wc = WordCloud(
                font_path=self.font_path,
                width=1200,
                height=600,
                background_color='white',
                max_words=50,
                stopwords=self.stop_words,
                colormap='viridis',
                contour_color='steelblue',
                contour_width=1,
                prefer_horizontal=0.7
            )
            wc.generate_from_frequencies(top_words)

            plt.figure(figsize=(12, 6), facecolor='white')
            plt.imshow(wc, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout(pad=0)

            if save_dir:
                img_path = Path(save_dir) / "wordcloud.png"
                plt.savefig(img_path, format='png', dpi=150, bbox_inches='tight')
                plt.close()
                return str(img_path), freq_file

            plt.close()
        except Exception as e:
            logging.error(f"词云生成失败: {e}")

        return None, freq_file

def generate_review_wordcloud(reviews, save_dir=None):
    """
    便捷函数：为评论生成词云

    Args:
        reviews: Review对象列表
        save_dir: 保存目录

    Returns:
        (词云图片路径, 词频文件路径) 或 (None, None)
    """
    generator = WordCloudGenerator()
    return generator.generate(reviews, save_dir)