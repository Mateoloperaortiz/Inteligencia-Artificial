"""Generate synthetic short reviews for restaurants using a local LLM integration.

Usage:
    python data/generate_reviews.py

This script reads `data/restaurants_sample.csv`, generates a short 1-2 sentence
review/explanation for each restaurant using `models.local_model_integration.generate_text`,
and writes results to `data/generated_reviews.csv` with columns: restaurant_id, generated_review.

If no local model is available, the script falls back to a template-based review.
"""

import argparse
import csv
import re
from typing import Optional

import pandas as pd

from models.local_model_integration import generate_text


def first_sentences(text: str, max_sentences: int = 2) -> str:
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return ' '.join(parts[:max_sentences]).strip()


def build_prompt(row: dict) -> str:
    name = row.get('name') or 'Este restaurante'
    cuisine = row.get('cuisine') or 'varios'
    address = row.get('address') or ''
    opening = row.get('opening_hours') or ''
    tags = row.get('tags') or ''
    prompt = (
        f"Eres un asistente conciso y amable. Genera una reseña muy corta (1-2 oraciones) en español "
        f"sobre este restaurante para un usuario que busca opciones locales. Restaurante: {name}. "
        f"Cocina: {cuisine}. Dirección: {address}. Horario (si se conoce): {opening}. Tags: {tags}. "
        "La reseña debe explicar brevemente por qué podría interesar y dar un consejo práctico (ej: 'reservar') si procede. "
        "Responde solo con la reseña en español."
    )
    return prompt


def fallback_review(row: dict) -> str:
    name = row.get('name') or 'Este restaurante'
    cuisine = row.get('cuisine') or 'cocina variada'
    return f"{name}: Cocina {cuisine}. Buena opción cercana; prueba su menú recomendado y considera reservar." 


def generate_for_df(df: pd.DataFrame) -> pd.DataFrame:
    reviews = []
    for _, row in df.iterrows():
        prompt = build_prompt(row)
        try:
            txt = generate_text(prompt, max_tokens=120)
        except Exception:
            txt = None

        if not txt:
            review = fallback_review(row)
        else:
            review = first_sentences(txt, max_sentences=2)

        reviews.append({
            'restaurant_id': row.get('id'),
            'generated_review': review,
        })

    return pd.DataFrame(reviews)


def main():
    p = argparse.ArgumentParser(description='Generate synthetic reviews for restaurants CSV')
    p.add_argument('--input', type=str, default='data/restaurants_sample.csv', help='Input CSV path')
    p.add_argument('--output', type=str, default='data/generated_reviews.csv', help='Output CSV path')
    args = p.parse_args()

    df = pd.read_csv(args.input)
    if df.empty:
        print('Input CSV is empty or not found:', args.input)
        return

    out_df = generate_for_df(df)
    out_df.to_csv(args.output, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f'Generated {len(out_df)} reviews and saved to {args.output}')


if __name__ == '__main__':
    main()
