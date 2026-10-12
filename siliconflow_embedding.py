"""
硅基流动Embedding客户端
使用BAAI/bge-m3模型进行文本向量化
"""

import os
import math
import requests


class SiliconFlowEmbedding:
    """硅基流动Embedding客户端"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("SILICONFLOW_API_KEY")
        if not self.api_key:
            raise ValueError("API密钥未设置！请设置 SILICONFLOW_API_KEY 环境变量")
        
        self.model = "BAAI/bge-m3"
        self.api_url = "https://api.siliconflow.cn/v1/embeddings"

    def embed(self, texts):
        """
        将文本向量化
        
        Args:
            texts: str 或 List[str]，要向量化的文本
        
        Returns:
            List[float] 或 List[List[float]]，嵌入向量
        """
        if isinstance(texts, str):
            texts = [texts]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": texts
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            embeddings = [item["embedding"] for item in result["data"]]
            
            return embeddings[0] if len(embeddings) == 1 else embeddings
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Embedding请求失败：{str(e)}")

    @staticmethod
    def cosine_similarity(vec1, vec2):
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1, vec2: List[float]，两个向量
        
        Returns:
            float，余弦相似度（0-1之间）
        """
        if len(vec1) != len(vec2):
            raise ValueError("向量维度不一致")
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class SemanticSearcher:
    """语义搜索器"""

    def __init__(self, embedding_client=None):
        self.embedding_client = embedding_client or SiliconFlowEmbedding()

    def build_knowledge_vectors(self, knowledge_base):
        """
        为知识库构建向量索引
        
        Args:
            knowledge_base: List[Dict]，知识库列表，每个元素需包含：
                - text: str，要向量化的文本
                - name: str，知识名称
                - type: str，知识类型
        
        Returns:
            List[Dict]，包含向量的知识库
        """
        print(f"正在为 {len(knowledge_base)} 条知识构建向量索引...")
        
        texts = [item["text"] for item in knowledge_base]
        embeddings = self.embedding_client.embed(texts)
        
        for i, item in enumerate(knowledge_base):
            item["embedding"] = embeddings[i]
        
        print(f"✓ 向量索引构建完成")
        return knowledge_base

    def semantic_search(self, query, knowledge_base, top_k=3, threshold=0.5):
        """
        语义搜索
        
        Args:
            query: str，用户查询
            knowledge_base: List[Dict]，已向量化的知识库
            top_k: int，返回前k个最相关结果
            threshold: float，相似度阈值
        
        Returns:
            List[Dict]，匹配到的知识列表，按相似度降序排列
        """
        print(f"\n🔍 正在搜索：{query}")
        
        query_embedding = self.embedding_client.embed(query)
        
        results = []
        for item in knowledge_base:
            similarity = self.embedding_client.cosine_similarity(
                query_embedding,
                item["embedding"]
            )
            
            if similarity >= threshold:
                results.append({
                    "name": item.get("name", ""),
                    "type": item.get("type", ""),
                    "text": item.get("text", ""),
                    "similarity": similarity
                })
        
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        print(f"✅ 找到 {len(results)} 条相关知识")
        for i, r in enumerate(results[:top_k], 1):
            print(f"  {i}. [{r['type']}] {r['name']} (相似度: {r['similarity']:.3f})")
        
        return results[:top_k]


def test_embedding():
    """测试Embedding功能"""
    print("=" * 60)
    print("      硅基流动Embedding功能测试")
    print("=" * 60)
    
    try:
        client = SiliconFlowEmbedding()
        print("✓ API密钥已配置")
        
        test_texts = [
            "物化是以确定性的框架来把握对方",
            "去物化是悬置自身需求，看到对方需求",
            "矛盾是关系的普遍引擎"
        ]
        
        print("\n正在测试文本向量化...")
        embeddings = client.embed(test_texts)
        print(f"✓ 成功向量化 {len(embeddings)} 条文本")
        
        print("\n正在测试相似度计算...")
        similarity = client.cosine_similarity(embeddings[0], embeddings[1])
        print(f"✓ 相似度计算成功：{similarity:.4f}")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败：{str(e)}")


if __name__ == "__main__":
    test_embedding()
