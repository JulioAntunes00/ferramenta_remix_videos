"""
Serviço responsável por calcular a similaridade estrutural entre vídeos gerados
e atribuir badges de alerta (Verde, Amarelo, Vermelho) para proteção Anti-Ban.
"""
from typing import Dict, List, Any


class SimilarityEvaluator:
    """
    Avalia a similaridade entre combinações de vídeos com base no percentual
    de tempo compartilhado (duração dos blocos comuns).
    
    Regras de Score:
    - VERDE: Similaridade máxima < 45% (baixo risco, ótimo para postagem)
    - AMARELO: 45% <= Similaridade máxima < 65% (atenção, espaçar postagens)
    - VERMELHO: Similaridade máxima >= 65% (alto risco de flag de duplicidade)
    """

    @staticmethod
    def evaluate_combinations(
        combinations: List[Dict[str, Any]], durations: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Recebe a lista de combinações e calcula o score relativo a cada outra combinação.
        Cada combinação possui chaves: 'id', 'hook', 'body', 'cta'.
        """
        results = []
        n = len(combinations)

        for i, comb_a in enumerate(combinations):
            max_similarity = 0.0
            most_similar_to = None

            dur_hook_a = durations.get(comb_a["hook"], 5.0)
            dur_body_a = durations.get(comb_a["body"], 10.0)
            dur_cta_a = durations.get(comb_a["cta"], 5.0)
            total_dur_a = max(dur_hook_a + dur_body_a + dur_cta_a, 0.1)

            for j, comb_b in enumerate(combinations):
                if i == j:
                    continue

                shared_dur = 0.0
                if comb_a["hook"] == comb_b["hook"]:
                    shared_dur += dur_hook_a
                if comb_a["body"] == comb_b["body"]:
                    shared_dur += dur_body_a
                if comb_a["cta"] == comb_b["cta"]:
                    shared_dur += dur_cta_a

                sim_ratio = (shared_dur / total_dur_a) * 100.0
                if sim_ratio > max_similarity:
                    max_similarity = sim_ratio
                    most_similar_to = comb_b["id"]

            # Classificação
            if max_similarity < 45.0:
                score_badge = "VERDE"
                recommendation = "Excelente para postar. Menos de 45% de conteúdo compartilhado."
            elif max_similarity < 65.0:
                score_badge = "AMARELO"
                recommendation = "Atenção: Espaçar a postagem deste vídeo em 24-48h de outros semelhantes."
            else:
                score_badge = "VERMELHO"
                recommendation = "Cuidado: Conteúdo muito similar a outro do mesmo lote. Risco de aviso no TikTok."

            results.append({
                **comb_a,
                "total_duration": round(total_dur_a, 2),
                "max_similarity_percent": round(max_similarity, 1),
                "most_similar_video_id": most_similar_to,
                "score_badge": score_badge,
                "recommendation": recommendation,
            })

        return results
