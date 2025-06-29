import json
import httpx
from typing import List, Optional
from models import TaskItem, CategoryItem, SummaryResponse


class GeminiService:
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    
    async def categorize_tasks(self, tasks: List[TaskItem]) -> SummaryResponse:
        if not self.api_key:
            return self._mock_categorize_tasks(tasks)
        
        prompt = self._build_categorization_prompt(tasks)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}?key={self.api_key}",
                json={
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 2048,
                    }
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Gemini API error: {response.status_code}")
            
            result = response.json()
            generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
            
            return self._parse_gemini_response(generated_text, tasks)
    
    def _build_categorization_prompt(self, tasks: List[TaskItem]) -> str:
        tasks_text = "\n".join([
            f"- {task.task_name} ({task.duration_ms}ms)"
            for task in tasks
        ])
        
        return f"""以下の作業リストを適切なカテゴリと小項目に分類してください。
各作業を1つのカテゴリと小項目に割り当て、JSON形式で回答してください。

作業リスト:
{tasks_text}

回答形式:
{{
  "categories": [
    {{
      "category": "開発",
      "subcategory": "フロントエンド",
      "tasks": ["作業名1", "作業名2"]
    }},
    {{
      "category": "会議",
      "subcategory": "設計レビュー", 
      "tasks": ["作業名3"]
    }}
  ]
}}

カテゴリの例: 開発、会議、学習、設計、テスト、デバッグ、ドキュメント作成、コードレビュー
小項目の例: フロントエンド、バックエンド、API、データベース、UI/UX、インフラ
"""
    
    def _parse_gemini_response(self, response_text: str, original_tasks: List[TaskItem]) -> SummaryResponse:
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_text = response_text[json_start:json_end]
            
            parsed_data = json.loads(json_text)
            categories = []
            
            task_duration_map = {task.task_name: task.duration_ms for task in original_tasks}
            
            for cat_data in parsed_data.get("categories", []):
                total_duration = sum(
                    task_duration_map.get(task_name, 0)
                    for task_name in cat_data.get("tasks", [])
                )
                
                categories.append(CategoryItem(
                    category=cat_data["category"],
                    subcategory=cat_data["subcategory"],
                    total_duration_ms=total_duration
                ))
            
            return SummaryResponse(categories=categories)
            
        except (json.JSONDecodeError, KeyError) as e:
            return self._mock_categorize_tasks(original_tasks)
    
    def _mock_categorize_tasks(self, tasks: List[TaskItem]) -> SummaryResponse:
        categories = []
        
        for task in tasks:
            if any(keyword in task.task_name.lower() for keyword in ['開発', 'コード', '実装', 'プログラム']):
                category = "開発"
                subcategory = "実装"
            elif any(keyword in task.task_name.lower() for keyword in ['テスト', 'test', 'デバッグ']):
                category = "開発" 
                subcategory = "テスト"
            elif any(keyword in task.task_name.lower() for keyword in ['会議', 'ミーティング', '打ち合わせ']):
                category = "会議"
                subcategory = "チーム会議"
            elif any(keyword in task.task_name.lower() for keyword in ['学習', '勉強', '調査', '研究']):
                category = "学習"
                subcategory = "技術調査"
            elif any(keyword in task.task_name.lower() for keyword in ['設計', 'design', '仕様']):
                category = "設計"
                subcategory = "システム設計"
            elif any(keyword in task.task_name.lower() for keyword in ['ドキュメント', '資料', '文書']):
                category = "ドキュメント作成"
                subcategory = "技術資料"
            else:
                category = "その他"
                subcategory = "一般作業"
            
            existing_category = next(
                (cat for cat in categories if cat.category == category and cat.subcategory == subcategory),
                None
            )
            
            if existing_category:
                existing_category.total_duration_ms += task.duration_ms
            else:
                categories.append(CategoryItem(
                    category=category,
                    subcategory=subcategory,
                    total_duration_ms=task.duration_ms
                ))
        
        return SummaryResponse(categories=categories)