import re

class PromptValidator:
    """Validates sprint task prompts before execution"""
    
    @classmethod
    def validate_prompt(cls, prompt: str) -> dict:
        """
        Run all validation checks on a prompt.
        Returns: {
            "is_valid": bool,
            "warnings": [str],  # non-blocking issues
            "errors": [str],    # blocking issues
            "score": float      # 0-1 quality score
        }
        """
        warnings = []
        errors = []
        
        warnings.extend(cls.check_self_contained(prompt))
        warnings.extend(cls.check_file_paths(prompt))
        errors.extend(cls.check_has_tests(prompt))
        warnings.extend(cls.check_has_acceptance_criteria(prompt))
        warnings.extend(cls.check_length(prompt))
        
        # Calculate quality score (0.0 to 1.0)
        score = 1.0
        score -= len(errors) * 0.3
        score -= len(warnings) * 0.1
        score = max(0.0, min(1.0, score))
        
        return {
            "is_valid": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
            "score": score
        }
    
    @staticmethod
    def check_self_contained(prompt: str) -> list[str]:
        """
        Check if prompt references prior context it won't have.
        Red flags:
        - "as we did before" / "as in the previous"
        - "using the same pattern"
        - "continue from" / "building on"
        - "the file we created" (without specifying which file)
        - References to "Step X" without full context
        Returns list of warning messages.
        """
        warnings = []
        prompt_lower = prompt.lower()
        red_flags = [
            "as we did before",
            "as in the previous",
            "using the same pattern",
            "continue from",
            "building on",
            "the file we created",
            "file we created earlier",
            "step "
        ]
        for flag in red_flags:
            if flag in prompt_lower:
                warnings.append(f"Prompt contains potential cross-task context reference: '{flag}'")
        return warnings
    
    @staticmethod
    def check_file_paths(prompt: str) -> list[str]:
        """
        Check if prompt specifies concrete file paths.
        Good: "Create backend/app/services/auth_service.py"
        Bad: "Create the auth service file"
        Returns warnings for vague file references.
        """
        # Regex to find common file path structures or file names with extensions
        file_path_pattern = re.compile(r'[a-zA-Z0-9_\-\/]+\.[a-zA-Z0-9_]+')
        matches = file_path_pattern.findall(prompt)
        
        warnings = []
        if not matches:
            warnings.append("Prompt does not seem to specify any concrete file paths (e.g. backend/app/main.py).")
        return warnings
    
    @staticmethod
    def check_has_tests(prompt: str) -> list[str]:
        """
        Check if prompt includes test cases.
        Should contain:
        - Test file path (e.g., tests/test_xxx.py)
        - Test function definitions
        - Test run command
        Returns errors if no tests found.
        """
        errors = []
        prompt_lower = prompt.lower()
        
        # Check for test file path
        has_test_file = False
        file_path_pattern = re.compile(r'[a-zA-Z0-9_\-\/]*test[a-zA-Z0-9_\-\/]*\.[a-zA-Z0-9_]+')
        if file_path_pattern.search(prompt_lower):
            has_test_file = True
            
        # Check for test function/definition
        has_test_def = False
        test_def_keywords = ["def test_", "async def test_", "test(", "describe(", "it(", "expect("]
        if any(keyword in prompt_lower for keyword in test_def_keywords):
            has_test_def = True
            
        if not has_test_file and not has_test_def:
            errors.append("Prompt is missing test cases or test file definitions.")
            
        return errors
    
    @staticmethod
    def check_has_acceptance_criteria(prompt: str) -> list[str]:
        """
        Check if prompt has clear acceptance criteria.
        Look for: "Acceptance Criteria", "must pass", "should work",
        specific assertions.
        """
        warnings = []
        prompt_lower = prompt.lower()
        acceptance_keywords = [
            "acceptance criteria",
            "must pass",
            "should work",
            "acceptance",
            "criteria",
            "must return",
            "should return",
            "requirements"
        ]
        if not any(keyword in prompt_lower for keyword in acceptance_keywords):
            warnings.append("Prompt is missing explicit acceptance criteria.")
        return warnings
    
    @staticmethod
    def check_length(prompt: str) -> list[str]:
        """
        Check prompt isn't too short (< 200 chars) or too long (> 15000 chars).
        Too short = probably missing detail.
        Too long = Claude might lose focus.
        """
        warnings = []
        length = len(prompt)
        if length < 200:
            warnings.append(f"Prompt is very short ({length} characters), it might be missing required details.")
        elif length > 15000:
            warnings.append(f"Prompt is very long ({length} characters), model might lose focus.")
        return warnings
    
    @classmethod
    def validate_all_prompts(cls, tasks: list[dict]) -> dict:
        """
        Validate all task prompts and return summary.
        Returns: {
            "total_tasks": int,
            "valid_tasks": int,
            "tasks_with_warnings": int,
            "tasks_with_errors": int,
            "overall_score": float,
            "task_results": [{"task_name": str, "is_valid": bool, "warnings": [...], "errors": [...]}]
        }
        """
        total_tasks = len(tasks)
        valid_tasks = 0
        tasks_with_warnings = 0
        tasks_with_errors = 0
        total_score = 0.0
        task_results = []
        
        for task in tasks:
            name = task.get("name") or task.get("task_name") or "Unnamed Task"
            prompt = task.get("prompt") or task.get("description") or ""
            res = cls.validate_prompt(prompt)
            
            is_valid = res["is_valid"]
            warnings = res["warnings"]
            errors = res["errors"]
            score = res["score"]
            
            if is_valid:
                valid_tasks += 1
            if errors:
                tasks_with_errors += 1
            if warnings:
                tasks_with_warnings += 1
                
            total_score += score
            
            task_results.append({
                "task_name": name,
                "is_valid": is_valid,
                "warnings": warnings,
                "errors": errors
            })
            
        overall_score = (total_score / total_tasks) if total_tasks > 0 else 1.0
        
        return {
            "total_tasks": total_tasks,
            "valid_tasks": valid_tasks,
            "tasks_with_warnings": tasks_with_warnings,
            "tasks_with_errors": tasks_with_errors,
            "overall_score": overall_score,
            "task_results": task_results
        }
