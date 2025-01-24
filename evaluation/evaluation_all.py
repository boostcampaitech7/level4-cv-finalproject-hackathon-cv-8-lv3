import sys
import os
import json
import evaluate
from collections import defaultdict
from sentence_transformers import SentenceTransformer
import numpy as np
from scipy import stats
from scipy.stats import pearsonr

def calculate_pearson_correlation(predictions_file, references_file):
    # 파일 로드 
    with open(predictions_file, 'r') as f:
        predictions = json.load(f)
    with open(references_file, 'r') as f:
        references = json.load(f)
    
    # 문장 임베딩을 위한 모델 로드
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    # 이미지별 점수를 저장할 리스트
    scores = []
    
    # 각 이미지 ID에 대해
    for img_info in references['images']:
        img_id = img_info['id']
        
        # 해당 이미지의 예측 캡션 찾기
        pred_caption = next((pred['caption'] for pred in predictions if pred['image_id'] == img_id), None)
        if pred_caption is None:
            continue
            
        # 해당 이미지의 참조 캡션들 찾기
        ref_captions = [ann['caption'] for ann in references['annotations'] if ann['image_id'] == img_id]
        if not ref_captions:
            continue
        
        # 예측 캡션과 참조 캡션들을 임베딩 벡터로 변환
        pred_emb = model.encode(pred_caption)
        ref_embs = [model.encode(ref) for ref in ref_captions]
        
        # 예측 캡션과 각 참조 캡션 간의 유사도 계산
        similarities = []
        for ref_emb in ref_embs:
            sim = np.dot(pred_emb, ref_emb) / (np.linalg.norm(pred_emb) * np.linalg.norm(ref_emb))
            similarities.append(sim)
        
        # 이미지별 점수 저장
        scores.append({
            'image_id': img_id,
            'pred_score': np.max(similarities),  # 가장 높은 유사도
            'ref_score': np.mean(similarities)   # 평균 유사도
        })
    
    if not scores:
        return 0
    
    # 점수 배열 생성
    pred_scores = [s['pred_score'] for s in scores]
    ref_scores = [s['ref_score'] for s in scores]
    
    # Pearson 상관계수 계산
    correlation, _ = pearsonr(pred_scores, ref_scores)
    
    return correlation  # 상관계수만 반환

def load_and_align_data(predictions_file, references_file):
    # 파일 로드
    with open(predictions_file, 'r') as f:
        predictions = json.load(f)
    with open(references_file, 'r') as f:
        references = json.load(f)
    
    # 이미지 ID별로 참조 캡션 그룹화
    ref_by_id = defaultdict(list)
    for ann in references['annotations']:
        ref_by_id[ann['image_id']].append(ann['caption'])
    
    # 정렬된 예측과 참조 리스트 생성
    aligned_predictions = []
    aligned_references = []
    
    for pred in predictions:
        img_id = pred['image_id']
        if img_id in ref_by_id:
            aligned_predictions.append(pred['caption'])
            aligned_references.append(ref_by_id[img_id])  # 해당 이미지의 모든 참조 캡션
    
    return aligned_predictions, aligned_references

def evaluate_all_metrics(predictions, references):
    # 메트릭 로드
    bertscore = evaluate.load('bertscore')
    bleu = evaluate.load('bleu')
    meteor = evaluate.load('meteor')
    rouge = evaluate.load('rouge')
    
    # 개별 문장 평가 결과를 저장할 리스트
    individual_results = []
    
    # 개별 문장 평가
    print("\n=== 개별 문장 평가 ===")
    for i, (pred, refs) in enumerate(zip(predictions, references)):
        # BLEU (이미 모든 참조 사용)
        bleu1 = bleu.compute(predictions=[pred], references=[refs], max_order=1)
        bleu4 = bleu.compute(predictions=[pred], references=[refs], max_order=4)
        
        # 각 참조 캡션에 대한 점수 계산
        meteor_scores = []
        rouge_scores = []
        bert_scores = []
        
        for ref in refs:
            meteor_result = meteor.compute(predictions=[pred], references=[ref])
            rouge_result = rouge.compute(predictions=[pred], references=[ref])
            bert_result = bertscore.compute(predictions=[pred], references=[ref], lang="en")
            
            meteor_scores.append(meteor_result['meteor'])
            rouge_scores.append(rouge_result['rougeL'])
            bert_scores.append(bert_result['f1'][0])
        
        # 개별 결과 저장
        individual_result = {
            "sentence_id": i + 1,
            "prediction": pred,
            "references": refs,
            "scores": {
                "bleu1": bleu1['bleu'],
                "bleu4": bleu4['bleu'],
                "meteor": max(meteor_scores),
                "rouge_l": max(rouge_scores),
                "bertscore_f1": max(bert_scores)
            }
        }
        individual_results.append(individual_result)
    
    # 전체 메트릭 계산
    all_meteor_scores = []
    all_rouge_scores = []
    all_bert_scores = []
    
    for pred, refs in zip(predictions, references):
        meteor_scores = []
        rouge_scores = []
        bert_scores = []
        
        for ref in refs:
            meteor_result = meteor.compute(predictions=[pred], references=[ref])
            rouge_result = rouge.compute(predictions=[pred], references=[ref])
            bert_result = bertscore.compute(predictions=[pred], references=[ref], lang="en")
            
            meteor_scores.append(meteor_result['meteor'])
            rouge_scores.append(rouge_result['rougeL'])
            bert_scores.append(bert_result['f1'][0])
        
        all_meteor_scores.append(max(meteor_scores))
        all_rouge_scores.append(max(rouge_scores))
        all_bert_scores.append(max(bert_scores))
    
    # BLEU 점수 계산 (모든 참조 사용)
    bleu1 = bleu.compute(predictions=predictions, references=references, max_order=1)
    bleu2 = bleu.compute(predictions=predictions, references=references, max_order=2)
    bleu3 = bleu.compute(predictions=predictions, references=references, max_order=3)
    bleu4 = bleu.compute(predictions=predictions, references=references, max_order=4)
    
    # true_pearson.py의 상관계수 계산
    correlation = calculate_pearson_correlation("blip-3_predictions.json", "references_gemini_fin.json")
    
    # 전체 결과를 JSON 형식으로 구성
    results = {
        "overall_scores": {
            "bleu": {
                "bleu1": float(bleu1['bleu']),
                "bleu2": float(bleu2['bleu']),
                "bleu3": float(bleu3['bleu']),
                "bleu4": float(bleu4['bleu'])
            },
            "meteor": float(np.mean(all_meteor_scores)),
            "rouge_l": float(np.mean(all_rouge_scores)),
            "bertscore_f1": float(np.mean(all_bert_scores)),
            "pearson_correlation": float(correlation)
        },
        "individual_scores": [
            {
                "sentence_id": result["sentence_id"],
                "prediction": result["prediction"],
                "references": result["references"],
                "scores": {
                    "bleu1": float(result["scores"]["bleu1"]),
                    "bleu4": float(result["scores"]["bleu4"]),
                    "meteor": float(result["scores"]["meteor"]),
                    "rouge_l": float(result["scores"]["rouge_l"]),
                    "bertscore_f1": float(result["scores"]["bertscore_f1"])
                }
            }
            for result in individual_results
        ]
    }
    
    # JSON 파일로 저장
    with open('evaluation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results

if __name__ == "__main__":
    predictions_file = "blip-3_predictions_fin.json"
    references_file = "gemini_predictions_fin.json"
    
    # 데이터 로드 및 정렬
    predictions, references = load_and_align_data(predictions_file, references_file)
    
    # 평가 실행 및 결과 저장
    results = evaluate_all_metrics(predictions, references)
    
    # 결과 출력
    print("\n=== 평가 결과 ===")
    print(json.dumps(results["overall_scores"], indent=2, ensure_ascii=False))