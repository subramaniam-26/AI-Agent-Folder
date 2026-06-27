import csv
import os
from collections import Counter
from typing import Any

from app.utils import normalize_soil_type

# Path to the dataset inside the workspace
DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset", "soil_data.csv")


def _normalized_key(value: str) -> str:
    """Return a stable lookup key for soil type comparisons."""
    return normalize_soil_type(value).casefold()


class DatasetLayer:
    def __init__(self, filepath: str = DATASET_PATH):
        self.filepath = filepath
        self.data: list[dict[str, Any]] = []
        self.load_data()

    def load_data(self):
        """Loads the dataset from the CSV file."""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Dataset file not found at {self.filepath}")

        with open(self.filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric values
                converted_row = {}
                for key, val in row.items():
                    key = key.strip()
                    val = val.strip() if val else ""
                    if key in ["nitrogen", "phosphorus", "potassium", "sulphur", "magnesium", "soil_health_score"]:
                        converted_row[key] = int(val) if val else 0
                    elif key in ["iron", "zinc", "copper", "boron", "ph", "organic_carbon", "electrical_conductivity"]:
                        converted_row[key] = float(val) if val else 0.0
                    else:
                        converted_row[key] = val
                self.data.append(converted_row)

    def filter_by_soil_type(self, soil_type: str) -> list[dict[str, Any]]:
        """Filters rows by normalized soil type."""
        normalized = _normalized_key(soil_type)
        return [
            row
            for row in self.data
            if _normalized_key(row.get("soil_type", "")) == normalized
        ]

    def get_supported_soil_types(self) -> list[str]:
        """Return all soil types available in the dataset."""
        return sorted({row.get("soil_type", "") for row in self.data if row.get("soil_type")})

    def _soil_not_found(self, soil_type: str) -> dict[str, Any]:
        return {
            "error": f"No data found for soil type '{soil_type}'",
            "supported_soil_types": self.get_supported_soil_types(),
        }

    def get_soil_statistics(self, soil_type: str) -> dict[str, Any]:
        """Calculates means for soil properties for a given soil type."""
        soil_type = normalize_soil_type(soil_type)
        rows = self.filter_by_soil_type(soil_type)
        if not rows:
            return self._soil_not_found(soil_type)

        num_rows = len(rows)
        keys = [
            "nitrogen", "phosphorus", "potassium", "sulphur", "iron",
            "zinc", "copper", "boron", "magnesium", "ph",
            "organic_carbon", "electrical_conductivity", "soil_health_score"
        ]

        means = {}
        for key in keys:
            total = sum(row.get(key, 0) for row in rows)
            means[key] = round(total / num_rows, 2)

        return {
            "soil_type": soil_type,
            "sample_count": num_rows,
            "averages": means
        }

    def get_soil_health_score(self, soil_type: str) -> dict[str, Any]:
        """Retrieves average health score and brief assessment."""
        soil_type = normalize_soil_type(soil_type)
        rows = self.filter_by_soil_type(soil_type)
        if not rows:
            return self._soil_not_found(soil_type)

        scores = [row.get("soil_health_score", 0) for row in rows]
        avg_score = round(sum(scores) / len(scores), 2)
        min_score = min(scores)
        max_score = max(scores)

        # Basic qualitative assessment based on health score
        if avg_score >= 80:
            condition = "Optimal / Healthy"
        elif avg_score >= 60:
            condition = "Moderate / Intermediate"
        else:
            condition = "Poor / Depleted"

        return {
            "soil_type": soil_type,
            "average_health_score": avg_score,
            "min_score": min_score,
            "max_score": max_score,
            "condition_assessment": condition
        }

    def get_soil_profile(self, soil_type: str, limit: int = 5) -> list[dict[str, Any]]:
        """Returns raw sample records/profiles for the soil type."""
        soil_type = normalize_soil_type(soil_type)
        rows = self.filter_by_soil_type(soil_type)
        return rows[:limit]

    def get_crop_recommendation(self, soil_type: str) -> dict[str, Any]:
        """Recommends a crop based on frequency in the dataset for a soil type."""
        soil_type = normalize_soil_type(soil_type)
        rows = self.filter_by_soil_type(soil_type)
        if not rows:
            return self._soil_not_found(soil_type)

        crops = [row.get("recommended_crop", "") for row in rows if row.get("recommended_crop")]
        if not crops:
            return {
                "recommended_crop": "Unknown",
                "confidence": 0.0,
                "reason": f"No crop recommendations found in the dataset for soil type '{soil_type}'."
            }

        counter = Counter(crops)
        most_common_crop, count = counter.most_common(1)[0]
        confidence = round(count / len(crops), 2)

        return {
            "recommended_crop": most_common_crop,
            "confidence": confidence,
            "frequency_distribution": dict(counter),
            "reason": f"Based on {len(crops)} historical records of soil type '{soil_type}', '{most_common_crop}' was recommended {count} times ({int(confidence * 100)}% of cases)."
        }

    def get_fertilizer_recommendation(self, soil_type: str) -> dict[str, Any]:
        """Recommends a fertilizer based on frequency in the dataset for a soil type."""
        soil_type = normalize_soil_type(soil_type)
        rows = self.filter_by_soil_type(soil_type)
        if not rows:
            return self._soil_not_found(soil_type)

        fertilizers = [row.get("recommended_fertilizer", "") for row in rows if row.get("recommended_fertilizer")]
        if not fertilizers:
            return {
                "recommended_fertilizer": "Unknown",
                "confidence": 0.0,
                "reason": f"No fertilizer recommendations found in the dataset for soil type '{soil_type}'."
            }

        counter = Counter(fertilizers)
        most_common_fert, count = counter.most_common(1)[0]
        confidence = round(count / len(fertilizers), 2)

        return {
            "recommended_fertilizer": most_common_fert,
            "confidence": confidence,
            "frequency_distribution": dict(counter),
            "reason": f"Based on {len(fertilizers)} historical records of soil type '{soil_type}', '{most_common_fert}' was recommended {count} times ({int(confidence * 100)}% of cases)."
        }

    def get_crop_profile(self, crop_name: str) -> dict[str, Any]:
        """Provides average conditions where this crop is recommended in the dataset."""
        normalized = crop_name.strip().lower()
        rows = [row for row in self.data if row.get("recommended_crop", "").strip().lower() == normalized]
        if not rows:
            return {"error": f"No historical records found for crop '{crop_name}'"}

        # Calculate average properties where this crop is successful
        keys = ["nitrogen", "phosphorus", "potassium", "ph", "organic_carbon", "soil_health_score"]
        averages = {}
        for key in keys:
            total = sum(row.get(key, 0) for row in rows)
            averages[key] = round(total / len(rows), 2)

        # Most common soil type for this crop
        soil_types = [row.get("soil_type", "") for row in rows if row.get("soil_type")]
        favored_soil = Counter(soil_types).most_common(1)[0][0] if soil_types else "Unknown"

        return {
            "crop_name": crop_name,
            "sample_records_count": len(rows),
            "typical_soil_properties": averages,
            "primary_soil_type": favored_soil,
            "description": f"Typical growing conditions for '{crop_name}' calculated from {len(rows)} samples in the dataset."
        }

    def get_fertilizer_profile(self, fertilizer_name: str) -> dict[str, Any]:
        """Provides average conditions where this fertilizer is recommended in the dataset."""
        normalized = fertilizer_name.strip().lower()
        rows = [row for row in self.data if row.get("recommended_fertilizer", "").strip().lower() == normalized]
        if not rows:
            return {"error": f"No historical records found for fertilizer '{fertilizer_name}'"}

        keys = ["nitrogen", "phosphorus", "potassium", "ph", "organic_carbon", "soil_health_score"]
        averages = {}
        for key in keys:
            total = sum(row.get(key, 0) for row in rows)
            averages[key] = round(total / len(rows), 2)

        soil_types = [row.get("soil_type", "") for row in rows if row.get("soil_type")]
        primary_soil = Counter(soil_types).most_common(1)[0][0] if soil_types else "Unknown"

        return {
            "fertilizer_name": fertilizer_name,
            "sample_records_count": len(rows),
            "typical_soil_properties": averages,
            "primary_soil_type": primary_soil,
            "description": f"Typical soil property profile where '{fertilizer_name}' is applied, based on {len(rows)} samples in the dataset."
        }
