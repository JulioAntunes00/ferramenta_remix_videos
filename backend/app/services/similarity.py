"""
Serviço responsável por calcular a similaridade estrutural entre vídeos gerados
e atribuir badges de alerta (Verde, Amarelo, Vermelho) para proteção Anti-Ban TikTok.
"""
from typing import Dict, List, Any


class SimilarityEvaluator:
    """
    Avalia a similaridade entre combinações de vídeos com peso algorítmico realista:
    - O Gancho (Hook) é o fator mais crítico para retenção e análise dos primeiros segundos do algoritmo.
    - Se dois vídeos compartilham APENAS o gancho ou APENAS o CTA, o score é VERDE (baixo risco).
    - Se dois vídeos compartilham o GANCHO + CORPO (ou seja, mais de 2 blocos ou mais de 75% do vídeo),
      ele se torna AMARELO ou VERMELHO dependendo do tempo exato.
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

        # Se houver apenas 1 vídeo, ele é único (100% verde)
        if n <= 1:
            for comb in combinations:
                results.append({
                    **comb,
                    "total_duration": 15.0,
                    "max_similarity_percent": 0.0,
                    "most_similar_video_id": None,
                    "score_badge": "VERDE",
                    "recommendation": "Vídeo único no lote. Baixíssimo risco algorítmico.",
                })
            return results

        for i, comb_a in enumerate(combinations):
            max_similarity = 0.0
            most_similar_to = None
            shared_parts_count = 0

            dur_hook_a = durations.get(comb_a["hook"], 4.0)
            dur_body_a = durations.get(comb_a["body"], 8.0)
            dur_cta_a = durations.get(comb_a["cta"], 3.0)
            total_dur_a = max(dur_hook_a + dur_body_a + dur_cta_a, 0.1)

            for j, comb_b in enumerate(combinations):
                if i == j:
                    continue

                shared_dur = 0.0
                parts_equal = 0

                if comb_a["hook"] == comb_b["hook"]:
                    shared_dur += dur_hook_a
                    parts_equal += 1
                if comb_a["body"] == comb_b["body"]:
                    shared_dur += dur_body_a
                    parts_equal += 1
                if comb_a["cta"] == comb_b["cta"]:
                    shared_dur += dur_cta_a
                    parts_equal += 1

                sim_ratio = (shared_dur / total_dur_a) * 100.0
                if sim_ratio > max_similarity:
                    max_similarity = sim_ratio
                    most_similar_to = comb_b["id"]
                    shared_parts_count = parts_equal

            # Regra de Classificação Realista para Criativos de Tráfego:
            # - Se compartilha apenas 1 bloco (ex: só o mesmo gancho com corpo e CTA diferentes),
            #   para o TikTok são criativos distintos -> VERDE.
            # - Se compartilha 2 blocos (ex: mesmo gancho e mesmo corpo, mudando só o CTA de 2s):
            #   -> Se a similaridade passar de 80%, é VERMELHO (muito repetitivo).
            #   -> Entre 50% e 80%, é AMARELO (espaçar postagens em 24h).
            # - Caso contrário -> VERDE.
            if shared_parts_count <= 1 or max_similarity < 55.0:
                score_badge = "VERDE"
                recommendation = "Ótimo para postar. Gancho e conteúdo bem diversificados dos demais."
            elif max_similarity < 80.0:
                score_badge = "AMARELO"
                recommendation = "Similaridade média. Recomendado espaçar a postagem deste vídeo em 24h a 48h."
            else:
                score_badge = "VERMELHO"
                recommendation = "Alta similaridade com outro vídeo (mais de 80% idêntico). Varie mais os ganchos/corpos."

            results.append({
                **comb_a,
                "total_duration": round(total_dur_a, 2),
                "max_similarity_percent": round(max_similarity, 1),
                "most_similar_video_id": most_similar_to,
                "score_badge": score_badge,
                "recommendation": recommendation,
            })

        return results
