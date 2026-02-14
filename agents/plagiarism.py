import ast
import hashlib
from typing import List, Dict, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlagiarismDetector:
    """
    AST-based and embedding-based plagiarism detection
    """
    
    def __init__(self):
        self.known_solutions = []  # Database of known solutions
        self.ast_cache = {}
        
    def detect(self, code: str, threshold: float = 0.8) -> Dict:
        """
        Detect plagiarism in code
        """
        results = {
            "similarity_score": 0,
            "matches": [],
            "method": "none",
            "details": {}
        }
        
        # Method 1: AST-based detection
        ast_similarity = self._check_ast_similarity(code)
        if ast_similarity["score"] > threshold:
            results["similarity_score"] = ast_similarity["score"]
            results["matches"] = ast_similarity["matches"]
            results["method"] = "ast"
            results["details"] = ast_similarity
            return results
        
        # Method 2: TF-IDF based detection
        tfidf_similarity = self._check_tfidf_similarity(code)
        if tfidf_similarity["score"] > threshold:
            results["similarity_score"] = tfidf_similarity["score"]
            results["matches"] = tfidf_similarity["matches"]
            results["method"] = "tfidf"
            results["details"] = tfidf_similarity
            return results
        
        # Method 3: Structure-based detection
        struct_similarity = self._check_structure_similarity(code)
        results["similarity_score"] = struct_similarity["score"]
        results["matches"] = struct_similarity["matches"]
        results["method"] = "structure"
        results["details"] = struct_similarity
        
        return results
    
    def _check_ast_similarity(self, code: str) -> Dict:
        """Compare AST structure"""
        try:
            # Parse code to AST
            tree = ast.parse(code)
            
            # Normalize AST (remove variable names, etc.)
            normalized_ast = self._normalize_ast(tree)
            ast_hash = hashlib.md5(str(normalized_ast).encode()).hexdigest()
            
            # Compare with known solutions
            matches = []
            for known in self.known_solutions:
                if known.get("ast_hash") == ast_hash:
                    matches.append({
                        "source": known.get("source", "unknown"),
                        "similarity": 1.0,
                        "method": "exact_ast_match"
                    })
            
            score = 1.0 if matches else 0.0
            
            return {
                "score": score,
                "matches": matches,
                "ast_hash": ast_hash
            }
        except Exception as e:
            logger.error(f"AST similarity error: {e}")
            return {"score": 0, "matches": [], "error": str(e)}
    
    def _normalize_ast(self, tree: ast.AST) -> ast.AST:
        """Normalize AST by removing variable names and literal values"""
        class NormalizeTransformer(ast.NodeTransformer):
            def visit_Name(self, node):
                # Replace variable names with placeholders
                node.id = "var"
                return node
            
            def visit_FunctionDef(self, node):
                node.name = "func"
                return self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                node.name = "Class"
                return self.generic_visit(node)
            
            def visit_Constant(self, node):
                # Replace constants with placeholders
                node.value = None
                return node
        
        transformer = NormalizeTransformer()
        return transformer.visit(tree)
    
    def _check_tfidf_similarity(self, code: str) -> Dict:
        """Compare using TF-IDF and cosine similarity"""
        if not self.known_solutions:
            return {"score": 0, "matches": []}
        
        # Prepare documents
        documents = [s["code"] for s in self.known_solutions] + [code]
        
        # Calculate TF-IDF
        vectorizer = TfidfVectorizer(
            analyzer='word',
            token_pattern=r'\w+',
            ngram_range=(1, 3),
            min_df=1
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(documents)
            
            # Calculate similarity with last document (query code)
            similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
            
            # Find matches above threshold
            matches = []
            for i, sim in enumerate(similarities):
                if sim > 0.7:  # Threshold
                    matches.append({
                        "source": self.known_solutions[i].get("source", "unknown"),
                        "similarity": float(sim),
                        "method": "tfidf"
                    })
            
            max_similarity = float(max(similarities)) if similarities.size > 0 else 0
            
            return {
                "score": max_similarity,
                "matches": matches
            }
        except Exception as e:
            logger.error(f"TF-IDF similarity error: {e}")
            return {"score": 0, "matches": []}
    
    def _check_structure_similarity(self, code: str) -> Dict:
        """Compare structural features"""
        try:
            # Extract structural features
            features = self._extract_structural_features(code)
            
            # Compare with known solutions
            matches = []
            for known in self.known_solutions:
                known_features = known.get("features", {})
                
                # Calculate structural similarity
                similarity = self._calculate_structural_similarity(features, known_features)
                
                if similarity > 0.8:
                    matches.append({
                        "source": known.get("source", "unknown"),
                        "similarity": similarity,
                        "method": "structural"
                    })
            
            max_similarity = max([m["similarity"] for m in matches]) if matches else 0
            
            return {
                "score": max_similarity,
                "matches": matches,
                "features": features
            }
        except Exception as e:
            logger.error(f"Structure similarity error: {e}")
            return {"score": 0, "matches": []}
    
    def _extract_structural_features(self, code: str) -> Dict:
        """Extract structural features from code"""
        features = {
            "num_functions": 0,
            "num_classes": 0,
            "num_loops": 0,
            "num_conditionals": 0,
            "avg_function_length": 0,
            "max_nesting_depth": 0,
            "imports": []
        }
        
        try:
            tree = ast.parse(code)
            
            # Count features
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    features["num_functions"] += 1
                elif isinstance(node, ast.ClassDef):
                    features["num_classes"] += 1
                elif isinstance(node, (ast.For, ast.While)):
                    features["num_loops"] += 1
                elif isinstance(node, (ast.If, ast.IfExp)):
                    features["num_conditionals"] += 1
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        features["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    features["imports"].append(node.module)
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
        
        return features
    
    def _calculate_structural_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity between two feature sets"""
        if not features1 or not features2:
            return 0.0
        
        # Compare numerical features
        numerical_scores = []
        for key in ["num_functions", "num_classes", "num_loops", "num_conditionals"]:
            if key in features1 and key in features2:
                # Normalized difference
                max_val = max(features1[key], features2[key])
                if max_val > 0:
                    diff = abs(features1[key] - features2[key]) / max_val
                    numerical_scores.append(1 - diff)
        
        # Compare imports (Jaccard similarity)
        imports1 = set(features1.get("imports", []))
        imports2 = set(features2.get("imports", []))
        
        if imports1 or imports2:
            intersection = len(imports1.intersection(imports2))
            union = len(imports1.union(imports2))
            import_similarity = intersection / union if union > 0 else 0
            numerical_scores.append(import_similarity)
        
        return sum(numerical_scores) / len(numerical_scores) if numerical_scores else 0
    
    def add_to_database(self, code: str, source: str):
        """Add a solution to the known solutions database"""
        try:
            # Extract AST hash
            tree = ast.parse(code)
            normalized = self._normalize_ast(tree)
            ast_hash = hashlib.md5(str(normalized).encode()).hexdigest()
            
            # Extract features
            features = self._extract_structural_features(code)
            
            self.known_solutions.append({
                "code": code,
                "source": source,
                "ast_hash": ast_hash,
                "features": features,
                "timestamp": import_datetime().datetime.now().isoformat()
            })
            
            logger.info(f"Added solution to database: {source}")
        except Exception as e:
            logger.error(f"Error adding to database: {e}")
    
    def import_datetime(self):
        """Helper to import datetime"""
        from datetime import datetime
        return datetime