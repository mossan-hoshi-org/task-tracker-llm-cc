import json
import httpx
from typing import List, Optional
from models import TaskItem, CategoryItem, SummaryResponse


class GeminiService:
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name or "gemini-2.5-flash"
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
    
    async def categorize_tasks(self, tasks: List[TaskItem], projects: List[str] = None) -> SummaryResponse:
        if not self.api_key:
            return self._mock_categorize_tasks(tasks, projects or [])
        
        prompt = self._build_categorization_prompt(tasks, projects or [])
        
        async with httpx.AsyncClient(timeout=30.0) as client:
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
    
    def _build_categorization_prompt(self, tasks: List[TaskItem], projects: List[str]) -> str:
        tasks_text = "\n".join([
            f"- {task.task_name} ({task.duration_ms}ms)"
            for task in tasks
        ])
        
        # プロジェクト一覧からカテゴリ候補を生成
        if projects:
            category_candidates = ', '.join(f'"{project}"' for project in projects) + ', "その他"'
            project_instruction = f"カテゴリは以下のプロジェクトから選択してください: {category_candidates}"
        else:
            category_candidates = '"その他"'
            project_instruction = "プロジェクトが指定されていないため、カテゴリは「その他」を使用してください。"
        
        return f"""以下の作業リストをプロジェクト（カテゴリ）と作業種類（小項目）に分類してください。
各作業を1つのカテゴリ（プロジェクト）と小項目（作業種類）に割り当て、JSON形式で回答してください。

作業リスト:
{tasks_text}

{project_instruction}

回答形式:
{{
  "categories": [
    {{
      "category": "プロジェクトA",
      "subcategory": "開発",
      "tasks": ["作業名1", "作業名2"]
    }},
    {{
      "category": "その他",
      "subcategory": "会議", 
      "tasks": ["作業名3"]
    }}
  ]
}}

小項目（作業種類）の例: 開発、会議、学習、設計、テスト、デバッグ、ドキュメント作成、コードレビュー、実装、調査、打ち合わせ
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
                total_duration = 0
                for task_name_with_duration in cat_data.get("tasks", []):
                    # Extract task name from "task_name (duration_ms)" format
                    if " (" in task_name_with_duration:
                        clean_task_name = task_name_with_duration.split(" (")[0]
                    else:
                        clean_task_name = task_name_with_duration
                    
                    total_duration += task_duration_map.get(clean_task_name, 0)
                
                categories.append(CategoryItem(
                    category=cat_data["category"],
                    subcategory=cat_data["subcategory"],
                    total_duration_ms=total_duration
                ))
            
            return SummaryResponse(categories=categories)
            
        except (json.JSONDecodeError, KeyError) as e:
            return self._mock_categorize_tasks(original_tasks, [])
    
    def _mock_categorize_tasks(self, tasks: List[TaskItem], projects: List[str]) -> SummaryResponse:
        categories = []
        
        for task in tasks:
            # プロジェクト（カテゴリ）の決定
            task_lower = task.task_name.lower()
            category = "その他"  # デフォルト
            
            # プロジェクト名がタスク名に含まれているかチェック
            for project in projects:
                if project.lower() in task_lower:
                    category = project
                    break
            
            # 作業種類（サブカテゴリ）の決定
            if any(keyword in task_lower for keyword in ['開発', 'コード', '実装', 'プログラム']):
                subcategory = "開発"
            elif any(keyword in task_lower for keyword in ['テスト', 'test', 'デバッグ']):
                subcategory = "テスト"
            elif any(keyword in task_lower for keyword in ['会議', 'ミーティング', '打ち合わせ']):
                subcategory = "会議"
            elif any(keyword in task_lower for keyword in ['学習', '勉強', '調査', '研究']):
                subcategory = "学習"
            elif any(keyword in task_lower for keyword in ['設計', 'design', '仕様']):
                subcategory = "設計"
            elif any(keyword in task_lower for keyword in ['ドキュメント', '資料', '文書']):
                subcategory = "ドキュメント作成"
            else:
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