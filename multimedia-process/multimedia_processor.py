#!/usr/bin/env python3
"""
멀티미디어 처리기 v1.0 (VM/Local용)
=====================================
네이버 블로그 크롤러의 이미지/비디오 URL에서 텍스트 추출

처리 항목:
1. 이미지 OCR (PaddleOCR)
2. 비디오 첫/마지막 프레임 OCR
3. 유튜브 자막 추출
4. Whisper 음성인식 (faster-whisper)

사용법:
    python multimedia_processor.py --input data/naver_blog_pm_v10_4_posts.csv

의존성:
    pip install paddlepaddle paddleocr faster-whisper youtube-transcript-api
    pip install opencv-python yt-dlp pandas tqdm pillow requests

작성일: 2025-11-26
"""

import os
import sys
import re
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

import pandas as pd
import numpy as np
import requests
from tqdm import tqdm
from PIL import Image
from io import BytesIO

# 시간대 설정
try:
    import pytz
    KST = pytz.timezone('Asia/Seoul')
except ImportError:
    KST = None

# ===========================
# 로깅 설정
# ===========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ===========================
# 라이브러리 가용성 체크
# ===========================
PADDLEOCR_AVAILABLE = False
FASTER_WHISPER_AVAILABLE = False
OPENCV_AVAILABLE = False
YOUTUBE_API_AVAILABLE = False

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ PaddleOCR 미설치: pip install paddlepaddle paddleocr")

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ faster-whisper 미설치: pip install faster-whisper")

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ OpenCV 미설치: pip install opencv-python")

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ youtube-transcript-api 미설치: pip install youtube-transcript-api")


# ===========================
# OCR 프로세서 (PaddleOCR)
# ===========================
class OCRProcessor:
    """PaddleOCR 기반 이미지 텍스트 추출"""
    
    def __init__(self, use_gpu: bool = False):
        self.ocr_engine = None
        if PADDLEOCR_AVAILABLE:
            try:
                logger.info("🔧 PaddleOCR 초기화 중...")
                self.ocr_engine = PaddleOCR(
                    use_angle_cls=True,
                    lang='korean',
                    use_gpu=use_gpu,
                    show_log=False
                )
                logger.info(f"✅ PaddleOCR 준비 완료 ({'GPU' if use_gpu else 'CPU'} 모드)")
            except Exception as e:
                logger.error(f"PaddleOCR 초기화 실패: {e}")
    
    def download_image(self, url: str, timeout: int = 15) -> Optional[np.ndarray]:
        """이미지 다운로드"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://blog.naver.com/'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            return np.array(image)
        except Exception as e:
            logger.debug(f"이미지 다운로드 실패: {e}")
            return None
    
    def perform_ocr(self, image_array: np.ndarray, min_confidence: float = 0.6) -> Tuple[str, float]:
        """OCR 수행"""
        if not self.ocr_engine:
            return "", 0.0
        
        try:
            result = self.ocr_engine.ocr(image_array, cls=True)
            if not result or not result[0]:
                return "", 0.0
            
            texts = []
            confidences = []
            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                if confidence >= min_confidence:
                    texts.append(text)
                    confidences.append(confidence)
            
            combined_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            return combined_text, avg_confidence
        except Exception as e:
            logger.debug(f"OCR 처리 실패: {e}")
            return "", 0.0


# ===========================
# 비디오 프레임 추출기
# ===========================
class VideoFrameExtractor:
    """비디오에서 첫/마지막 프레임 추출"""
    
    def __init__(self, temp_dir: str = "temp_videos"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
    
    def download_video(self, url: str, save_path: str, timeout: int = 60) -> bool:
        """비디오 다운로드"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://blog.naver.com/'
            }
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            return False
        except Exception as e:
            logger.debug(f"비디오 다운로드 실패: {e}")
            return False
    
    def extract_frames(self, video_path: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """첫 프레임과 마지막 프레임 추출"""
        if not OPENCV_AVAILABLE:
            return None, None
        
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 첫 프레임 (5프레임 스킵)
            first_frame = None
            for _ in range(5):
                cap.read()
            ret, frame = cap.read()
            if ret:
                first_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 마지막 프레임
            last_frame = None
            if total_frames > 10:
                cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 5)
                ret, frame = cap.read()
                if ret:
                    last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            cap.release()
            return first_frame, last_frame
        except Exception as e:
            logger.debug(f"프레임 추출 실패: {e}")
            return None, None
    
    def cleanup(self, video_path: str):
        """임시 파일 삭제"""
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
        except:
            pass


# ===========================
# Whisper 음성인식 (faster-whisper)
# ===========================
class WhisperProcessor:
    """faster-whisper 기반 음성인식"""
    
    def __init__(self, model_size: str = "medium", device: str = "cpu", compute_type: str = "int8"):
        self.model = None
        if FASTER_WHISPER_AVAILABLE:
            try:
                logger.info(f"🔧 Faster-Whisper 모델 로딩 중 ({model_size})...")
                self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
                logger.info(f"✅ Faster-Whisper 준비 완료 ({device}/{compute_type})")
            except Exception as e:
                logger.error(f"Faster-Whisper 초기화 실패: {e}")
    
    def transcribe(self, audio_path: str, language: str = "ko") -> Tuple[str, str]:
        """음성인식 수행"""
        if not self.model:
            return "", "model_not_available"
        
        try:
            segments, info = self.model.transcribe(
                audio_path,
                beam_size=5,
                language=language,
                vad_filter=True,  # 핵심: 무음/음악 구간 스킵
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            text_list = []
            for segment in segments:
                text_list.append(segment.text)
            
            return " ".join(text_list), "success"
        except Exception as e:
            logger.debug(f"Whisper 처리 실패: {e}")
            return "", f"error: {str(e)[:50]}"


# ===========================
# 유튜브 자막 추출기
# ===========================
class YouTubeTranscriptExtractor:
    """유튜브 자막 API 기반 추출"""
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """URL에서 video_id 추출"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_transcript(self, video_id: str) -> Tuple[str, str, str]:
        """자막 추출 (transcript, language, status)"""
        if not YOUTUBE_API_AVAILABLE:
            return "", "", "api_not_available"
        
        try:
            # 한국어 우선 시도
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
                language = 'ko'
            except:
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                    language = 'en'
                except:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                    language = 'auto'
            
            full_transcript = ' '.join([item['text'] for item in transcript_list])
            return full_transcript, language, "success"
        
        except TranscriptsDisabled:
            return "", "", "transcripts_disabled"
        except NoTranscriptFound:
            return "", "", "no_transcript"
        except Exception as e:
            return "", "", f"error: {str(e)[:50]}"


# ===========================
# URL 추출기
# ===========================
class URLExtractor:
    """크롤링 결과에서 이미지/비디오 URL 추출"""
    
    @staticmethod
    def extract_from_csv(csv_path: str, output_dir: str = ".") -> Tuple[str, str]:
        """CSV에서 이미지/비디오 URL 추출 후 별도 파일로 저장"""
        df = pd.read_csv(csv_path)
        output_dir = Path(output_dir)
        
        # 이미지 URL 추출
        image_data = []
        if 'image_urls' in df.columns:
            for idx, row in df.iterrows():
                post_id = row.get('post_id', idx)
                urls = row.get('image_urls', '')
                if pd.notna(urls) and urls:
                    for url in str(urls).split(','):
                        url = url.strip()
                        if url:
                            image_data.append({'post_id': post_id, 'url': url})
        
        image_df = pd.DataFrame(image_data)
        image_path = output_dir / 'extracted_image_urls.csv'
        image_df.to_csv(image_path, index=False, encoding='utf-8-sig')
        logger.info(f"💾 이미지 URL 저장: {image_path} ({len(image_df)}개)")
        
        # 비디오 URL 추출
        video_data = []
        if 'video_urls' in df.columns:
            for idx, row in df.iterrows():
                post_id = row.get('post_id', idx)
                urls = row.get('video_urls', '')
                if pd.notna(urls) and urls:
                    for url in str(urls).split(','):
                        url = url.strip()
                        if url:
                            video_type = 'youtube' if 'youtube' in url or 'youtu.be' in url else 'naver_blog'
                            video_id = YouTubeTranscriptExtractor.extract_video_id(url) if video_type == 'youtube' else ''
                            video_data.append({
                                'post_id': post_id, 
                                'url': url, 
                                'type': video_type,
                                'youtube_video_id': video_id
                            })
        
        video_df = pd.DataFrame(video_data)
        video_path = output_dir / 'extracted_video_urls.csv'
        video_df.to_csv(video_path, index=False, encoding='utf-8-sig')
        logger.info(f"💾 비디오 URL 저장: {video_path} ({len(video_df)}개)")
        
        return str(image_path), str(video_path)


# ===========================
# 메인 프로세서
# ===========================
class MultimediaProcessor:
    """멀티미디어 통합 처리기"""
    
    def __init__(self, use_gpu: bool = False, whisper_model: str = "medium"):
        self.ocr = OCRProcessor(use_gpu=use_gpu)
        self.video_extractor = VideoFrameExtractor()
        self.whisper = WhisperProcessor(
            model_size=whisper_model,
            device="cuda" if use_gpu else "cpu",
            compute_type="float16" if use_gpu else "int8"
        )
        self.youtube = YouTubeTranscriptExtractor()
        
        self.stats = {
            'image_total': 0,
            'image_success': 0,
            'image_with_text': 0,
            'video_total': 0,
            'video_frame_success': 0,
            'youtube_transcript_success': 0,
            'whisper_success': 0,
            'start_time': None,
            'end_time': None
        }
    
    def process_images(self, image_csv: str, output_path: str) -> pd.DataFrame:
        """이미지 OCR 일괄 처리"""
        logger.info("=" * 70)
        logger.info("📸 이미지 OCR 처리 시작")
        logger.info("=" * 70)
        
        df = pd.read_csv(image_csv)
        self.stats['image_total'] = len(df)
        results = []
        
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="이미지 OCR"):
            post_id = row['post_id']
            url = row['url']
            
            image = self.ocr.download_image(url)
            if image is not None:
                ocr_text, confidence = self.ocr.perform_ocr(image)
                status = 'success'
                self.stats['image_success'] += 1
                if ocr_text:
                    self.stats['image_with_text'] += 1
            else:
                ocr_text, confidence = "", 0.0
                status = 'download_failed'
            
            results.append({
                'post_id': post_id,
                'url': url,
                'ocr_text': ocr_text,
                'confidence': confidence,
                'status': status
            })
            time.sleep(0.1)
        
        result_df = pd.DataFrame(results)
        result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"✅ 이미지 OCR 완료: {self.stats['image_success']}/{self.stats['image_total']}")
        logger.info(f"💾 저장: {output_path}")
        return result_df
    
    def process_video_frames(self, video_csv: str, output_path: str) -> pd.DataFrame:
        """비디오 프레임 OCR 처리"""
        logger.info("=" * 70)
        logger.info("🎬 비디오 프레임 OCR 처리 시작")
        logger.info("=" * 70)
        
        df = pd.read_csv(video_csv)
        naver_videos = df[df['type'] == 'naver_blog']
        results = []
        
        for idx, row in tqdm(naver_videos.iterrows(), total=len(naver_videos), desc="비디오 프레임 OCR"):
            post_id = row['post_id']
            url = row['url']
            
            video_path = str(self.video_extractor.temp_dir / f"video_{post_id}.mp4")
            
            if self.video_extractor.download_video(url, video_path):
                first_frame, last_frame = self.video_extractor.extract_frames(video_path)
                
                first_ocr = ""
                last_ocr = ""
                
                if first_frame is not None:
                    first_ocr, _ = self.ocr.perform_ocr(first_frame)
                if last_frame is not None:
                    last_ocr, _ = self.ocr.perform_ocr(last_frame)
                
                combined_ocr = f"{first_ocr} | {last_ocr}".strip(" |")
                status = 'success' if (first_ocr or last_ocr) else 'no_text'
                self.stats['video_frame_success'] += 1
                
                self.video_extractor.cleanup(video_path)
            else:
                combined_ocr = ""
                status = 'download_failed'
            
            results.append({
                'post_id': post_id,
                'url': url,
                'frame_ocr_text': combined_ocr,
                'status': status
            })
            time.sleep(0.2)
        
        result_df = pd.DataFrame(results)
        result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"✅ 비디오 프레임 OCR 완료: {self.stats['video_frame_success']}/{len(naver_videos)}")
        logger.info(f"💾 저장: {output_path}")
        return result_df
    
    def process_youtube_transcripts(self, video_csv: str, output_path: str) -> pd.DataFrame:
        """유튜브 자막 추출"""
        logger.info("=" * 70)
        logger.info("📺 유튜브 자막 추출 시작")
        logger.info("=" * 70)
        
        df = pd.read_csv(video_csv)
        youtube_videos = df[df['type'] == 'youtube']
        self.stats['video_total'] = len(df)
        results = []
        
        for idx, row in tqdm(youtube_videos.iterrows(), total=len(youtube_videos), desc="유튜브 자막"):
            post_id = row['post_id']
            url = row['url']
            video_id = row.get('youtube_video_id', '')
            
            if not video_id:
                video_id = self.youtube.extract_video_id(url)
            
            if video_id:
                transcript, language, status = self.youtube.get_transcript(video_id)
                if status == 'success':
                    self.stats['youtube_transcript_success'] += 1
            else:
                transcript, language, status = "", "", "no_video_id"
            
            results.append({
                'post_id': post_id,
                'url': url,
                'video_id': video_id,
                'transcript': transcript,
                'language': language,
                'status': status
            })
        
        result_df = pd.DataFrame(results)
        result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"✅ 유튜브 자막 추출 완료: {self.stats['youtube_transcript_success']}/{len(youtube_videos)}")
        logger.info(f"💾 저장: {output_path}")
        return result_df
    
    def process_whisper(self, video_csv: str, youtube_results: pd.DataFrame, output_path: str) -> pd.DataFrame:
        """Whisper 음성인식 (자막 없는 영상 대상)"""
        logger.info("=" * 70)
        logger.info("🎙️ Whisper 음성인식 처리 시작")
        logger.info("=" * 70)
        
        # 자막 없는 유튜브 + 네이버 비디오 대상
        df = pd.read_csv(video_csv)
        naver_videos = df[df['type'] == 'naver_blog']
        
        youtube_no_transcript = youtube_results[
            youtube_results['status'] != 'success'
        ]['video_id'].tolist() if len(youtube_results) > 0 else []
        
        logger.info(f"처리 대상: 자막없는 유튜브 {len(youtube_no_transcript)}개, 네이버 {len(naver_videos)}개")
        
        results = []
        
        # 네이버 비디오 Whisper
        for idx, row in tqdm(naver_videos.iterrows(), total=len(naver_videos), desc="네이버 Whisper"):
            post_id = row['post_id']
            url = row['url']
            
            video_path = str(self.video_extractor.temp_dir / f"whisper_{post_id}.mp4")
            
            if self.video_extractor.download_video(url, video_path, timeout=120):
                transcript, status = self.whisper.transcribe(video_path)
                if status == 'success':
                    self.stats['whisper_success'] += 1
                self.video_extractor.cleanup(video_path)
            else:
                transcript, status = "", "download_failed"
            
            results.append({
                'post_id': post_id,
                'url': url,
                'type': 'naver_blog',
                'transcript': transcript,
                'status': status
            })
            time.sleep(1)
        
        result_df = pd.DataFrame(results)
        result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"✅ Whisper 음성인식 완료: {self.stats['whisper_success']}/{len(results)}")
        logger.info(f"💾 저장: {output_path}")
        return result_df
    
    def generate_report(self, output_dir: str, crawler_version: str = "v10_4"):
        """처리 결과 리포트 생성"""
        now = datetime.now(KST) if KST else datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds() if self.stats['end_time'] else 0
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"📊 멀티미디어 처리 결과 리포트")
        report_lines.append(f"   크롤러 버전: {crawler_version}")
        report_lines.append(f"   생성일시: {now.strftime('%Y-%m-%d %H:%M:%S')} (KST)")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # 실행 시간
        report_lines.append("⏱️  실행 시간")
        report_lines.append("-" * 80)
        report_lines.append(f"• 총 실행 시간: {duration/60:.1f}분 ({int(duration)}초)")
        if self.stats['start_time']:
            report_lines.append(f"• 시작 시간: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        if self.stats['end_time']:
            report_lines.append(f"• 종료 시간: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 이미지 OCR 결과
        report_lines.append("📸 이미지 OCR 결과")
        report_lines.append("-" * 80)
        report_lines.append(f"• 전체: {self.stats['image_total']}개")
        if self.stats['image_total'] > 0:
            report_lines.append(f"• 성공: {self.stats['image_success']}개 ({self.stats['image_success']/self.stats['image_total']*100:.1f}%)")
            report_lines.append(f"• 텍스트 추출: {self.stats['image_with_text']}개 ({self.stats['image_with_text']/self.stats['image_total']*100:.1f}%)")
        report_lines.append("")
        
        # 비디오 처리 결과
        report_lines.append("🎬 비디오 처리 결과")
        report_lines.append("-" * 80)
        report_lines.append(f"• 전체: {self.stats['video_total']}개")
        report_lines.append(f"• 프레임 OCR 성공: {self.stats['video_frame_success']}개")
        report_lines.append(f"• 유튜브 자막 추출: {self.stats['youtube_transcript_success']}개")
        report_lines.append(f"• Whisper 음성인식: {self.stats['whisper_success']}개")
        report_lines.append("")
        
        # 생성된 파일
        report_lines.append("📁 생성된 파일")
        report_lines.append("-" * 80)
        report_lines.append(f"• image_ocr_results.csv")
        report_lines.append(f"• video_frame_ocr_results.csv")
        report_lines.append(f"• youtube_transcript_results.csv")
        report_lines.append(f"• whisper_transcript_results.csv")
        report_lines.append("")
        report_lines.append("=" * 80)
        
        # 저장
        report_path = Path(output_dir) / f"multimedia_processing_report_{now.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"💾 리포트 저장: {report_path}")
        
        # 콘솔 출력
        print()
        for line in report_lines:
            print(line)
    
    def run_all(self, input_csv: str, output_dir: str = ".", crawler_version: str = "v10_4"):
        """전체 파이프라인 실행"""
        self.stats['start_time'] = datetime.now(KST) if KST else datetime.now()
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        logger.info("🚀 멀티미디어 처리 시작")
        logger.info(f"   입력: {input_csv}")
        logger.info(f"   출력: {output_dir}")
        
        # Step 1: URL 추출
        image_csv, video_csv = URLExtractor.extract_from_csv(input_csv, output_dir)
        
        # Step 2: 이미지 OCR
        self.process_images(image_csv, output_dir / 'image_ocr_results.csv')
        
        # Step 3: 비디오 프레임 OCR
        self.process_video_frames(video_csv, output_dir / 'video_frame_ocr_results.csv')
        
        # Step 4: 유튜브 자막
        youtube_df = self.process_youtube_transcripts(video_csv, output_dir / 'youtube_transcript_results.csv')
        
        # Step 5: Whisper 음성인식
        self.process_whisper(video_csv, youtube_df, output_dir / 'whisper_transcript_results.csv')
        
        self.stats['end_time'] = datetime.now(KST) if KST else datetime.now()
        
        # Step 6: 리포트 생성
        self.generate_report(output_dir, crawler_version)
        
        logger.info("🎉 모든 처리 완료!")


# ===========================
# 메인 함수
# ===========================
def main():
    parser = argparse.ArgumentParser(description='멀티미디어 처리기 (PaddleOCR + Faster-Whisper)')
    parser.add_argument('--input', '-i', required=True, help='입력 CSV 파일 경로')
    parser.add_argument('--output', '-o', default='.', help='출력 디렉토리 (기본: 현재 폴더)')
    parser.add_argument('--gpu', action='store_true', help='GPU 사용')
    parser.add_argument('--whisper-model', default='medium', choices=['tiny', 'base', 'small', 'medium', 'large-v3'],
                        help='Whisper 모델 크기 (기본: medium)')
    parser.add_argument('--version', '-v', default='v10_4', help='크롤러 버전 (리포트용)')
    
    args = parser.parse_args()
    
    processor = MultimediaProcessor(use_gpu=args.gpu, whisper_model=args.whisper_model)
    processor.run_all(args.input, args.output, args.version)


if __name__ == "__main__":
    main()
