from PIL import Image
import imagehash
import os
import numpy as np
import base64
import io
import pickle
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class IconMatch:
    caption: str
    similarity: float

@dataclass
class BatchMatchResult:
    matches: List[Optional[IconMatch]]
    
    def __str__(self):
        result = []
        for i, match in enumerate(self.matches):
            if match:
                result.append(f"Image {i}: Caption: '{match.caption}' (similarity: {match.similarity:.2%})")
            else:
                result.append(f"Image {i}: No match found")
        return "\n".join(result)

class IconMatcher:
    def __init__(self, similarity_threshold: float = 0.85):
        self.phash_database: Dict[str, Tuple[str, str]] = {}
        self.similarity_threshold = similarity_threshold

    def compute_phash(self, image_data: Image.Image) -> Optional[str]:
        """
        Compute perceptual hash from PIL Image object
        """
        try:
            return str(imagehash.phash(image_data))
        except Exception as e:
            print(f"Error computing hash: {str(e)}")
            return None

    def build_database_from_folder(self, icon_folder: str) -> None:
        """
        Build hash database from a folder of images
        """
        for filename in os.listdir(icon_folder):
            filepath = os.path.join(icon_folder, filename)
            if os.path.isfile(filepath):
                try:
                    with Image.open(filepath).convert('RGB') as img:
                        hash_value = self.compute_phash(img)
                        if hash_value is not None:
                            self.phash_database[hash_value] = (filename, filename)
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")

    def save_database(self, filepath: str | os.PathLike) -> None:
        """
        Save the hash database to a file
        """
        with open(str(filepath), 'wb') as f:
            pickle.dump(self.phash_database, f)

    def load_database(self, filepath: str | os.PathLike) -> None:
        """
        Load the hash database from a file
        """
        with open(str(filepath), 'rb') as f:
            self.phash_database = pickle.load(f)

    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> int:
        """
        Calculate Hamming distance between two hash strings
        """
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

    @staticmethod
    def base64_to_image(base64_str: str) -> Image.Image:
        """
        Convert base64 string to PIL Image
        """
        img_data = base64.b64decode(base64_str)
        return Image.open(io.BytesIO(img_data)).convert('RGB')

    def insert_images(self, image_data: List[Tuple[str, str]]) -> None:
        """
        Add new images to the database
        Args:
            image_data: List of tuples (base64_image, caption)
        """
        for base64_str, caption in image_data:
            try:
                img = self.base64_to_image(base64_str)
                hash_value = self.compute_phash(img)
                if hash_value is not None:
                    self.phash_database[hash_value] = (base64_str, caption)
            except Exception as e:
                print(f"Error processing image with caption '{caption}': {str(e)}")

    def find_matches_batch(self, base64_images: List[str]) -> BatchMatchResult:
        """
        Find matches for a batch of base64-encoded images
        Returns a BatchMatchResult object containing matches or None for each input image
        """
        db_hashes = np.array([[int(c) for c in bin(int(h, 16))[2:].zfill(64)] 
                             for h in self.phash_database.keys()])
        
        results = []
        for base64_str in base64_images:
            try:
                img = self.base64_to_image(base64_str)
                query_hash = self.compute_phash(img)
                
                if query_hash is None:
                    results.append(None)
                    continue

                query_array = np.array([int(c) for c in bin(int(query_hash, 16))[2:].zfill(64)])
                distances = np.sum(db_hashes != query_array, axis=1)
                
                min_distance = np.min(distances)
                if min_distance <= len(query_hash) * (1 - self.similarity_threshold):
                    best_match_idx = np.argmin(distances)
                    matched_hash = list(self.phash_database.keys())[best_match_idx]
                    similarity = 1 - (min_distance / len(query_hash))
                    _, caption = self.phash_database[matched_hash]
                    results.append(IconMatch(
                        caption=caption,
                        similarity=similarity
                    ))
                else:
                    results.append(None)
                    
            except Exception as e:
                print(f"Error processing image: {str(e)}")
                results.append(None)
                
        return BatchMatchResult(matches=results)


"""
        icon_matcher_config = config['captioning']['claude']['icon_matcher']
        self.icon_matcher = IconMatcher(
            similarity_threshold=icon_matcher_config['similarity_threshold']
        )
        self.icon_matcher.load_database(icon_matcher_config['database_path'])
"""