#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git 저장소 정리 스크립트
========================

Git에 올리기 전에 불필요한 파일을 정리하고 구조를 최적화합니다.

실행 방법:
    python cleanup_for_git.py
"""

import os
import shutil
from pathlib import Path

# 현재 스크립트 위치 기준
BASE_DIR = Path(__file__).parent

# 삭제할 파일/폴더 목록
TO_DELETE = [
    # Python 캐시
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    
    # 가상 환경
    '.venv',
    'venv',
    'ENV',
    
    # IDE
    '.vscode',
    '.idea',
    
    # OS
    '.DS_Store',
    'Thumbs.db',
    'desktop.ini',
    
    # 임시 파일
    '*.tmp',
    '*.temp',
    '*.log',
    
    # 아카이브
    'archive',
]

# naver_blog 폴더에서 삭제할 문서 (중복/불필요)
NAVER_BLOG_DOCS_TO_DELETE = [
    'CODE_FIXES_SUMMARY.md',
    'DIAGNOSIS_REPORT.md',
    'FEATURE_CHANGES.md',
    'IMPLEMENTATION_SUMMARY.md',
    'IMPROVEMENTS_SUMMARY.md',
    'README_NEW.md',
    'CHANGELOG.md',
    'INSTALL_GUIDE.md',
    'SETUP_GUIDE.md',
    'USAGE_GUIDE.md',
    'WHISPER_SETUP.md',
]

# naver_blog 폴더에서 삭제할 스크립트 (테스트/분석용)
NAVER_BLOG_SCRIPTS_TO_DELETE = [
    'analyze_hashtags.py',
    'check_hashtag_count.py',
    'check_hashtag_detailed.py',
    'comprehensive_analysis.py',
    'estimate_hashtag_total.py',
    'hashtag_direct_search.py',
    'organize_project.py',
    'test_hashtag_search.py',
    'test_selectors.py',
    'popularity_analyzer.py',
    'video_processor.py',
]

# 유지할 핵심 파일
KEEP_FILES = [
    'naver_blog_crawler_v5.py',
    'naver_blog_crawler_v6.py',
    'requirements_v5.txt',
    'config.example.py',
    '.env.example',
    '.gitignore',
    'README.md',
    'FINAL_SUMMARY.md',
    'NAVER_API_FIELDS.md',
    'PARTNER_IDENTIFICATION_GUIDE.md',
    'POPULARITY_METRICS_GUIDE.md',
    'PROJECT_STRUCTURE.md',
    'SEARCH_STRATEGY_COMPARISON.md',
]


def delete_pattern(base_path: Path, pattern: str):
    """패턴에 맞는 파일/폴더 삭제"""
    deleted = []
    
    if '*' in pattern:
        # 와일드카드 패턴
        for item in base_path.rglob(pattern):
            try:
                if item.is_file():
                    item.unlink()
                    deleted.append(str(item.relative_to(BASE_DIR)))
            except Exception as e:
                print(f"⚠ 삭제 실패: {item} - {e}")
    else:
        # 폴더/파일 이름
        for item in base_path.rglob(pattern):
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                    deleted.append(str(item.relative_to(BASE_DIR)))
                elif item.is_file():
                    item.unlink()
                    deleted.append(str(item.relative_to(BASE_DIR)))
            except Exception as e:
                print(f"⚠ 삭제 실패: {item} - {e}")
    
    return deleted


def cleanup_naver_blog():
    """naver_blog 폴더 정리"""
    naver_blog_dir = BASE_DIR / 'naver_blog'
    
    if not naver_blog_dir.exists():
        print("⚠ naver_blog 폴더를 찾을 수 없습니다.")
        return
    
    deleted = []
    
    # 불필요한 문서 삭제
    print("\n📄 불필요한 문서 삭제 중...")
    for doc in NAVER_BLOG_DOCS_TO_DELETE:
        doc_path = naver_blog_dir / doc
        if doc_path.exists():
            try:
                doc_path.unlink()
                deleted.append(f"naver_blog/{doc}")
                print(f"  ✓ 삭제: {doc}")
            except Exception as e:
                print(f"  ⚠ 삭제 실패: {doc} - {e}")
    
    # 불필요한 스크립트 삭제
    print("\n🔧 테스트/분석 스크립트 삭제 중...")
    for script in NAVER_BLOG_SCRIPTS_TO_DELETE:
        script_path = naver_blog_dir / script
        if script_path.exists():
            try:
                script_path.unlink()
                deleted.append(f"naver_blog/{script}")
                print(f"  ✓ 삭제: {script}")
            except Exception as e:
                print(f"  ⚠ 삭제 실패: {script} - {e}")
    
    # 빈 폴더 삭제
    print("\n📁 빈 폴더 삭제 중...")
    for folder in ['core', 'utils', 'docs', 'archive']:
        folder_path = naver_blog_dir / folder
        if folder_path.exists() and folder_path.is_dir():
            if not any(folder_path.iterdir()):
                try:
                    folder_path.rmdir()
                    deleted.append(f"naver_blog/{folder}/")
                    print(f"  ✓ 삭제: {folder}/")
                except Exception as e:
                    print(f"  ⚠ 삭제 실패: {folder}/ - {e}")
    
    return deleted


def main():
    print("=" * 70)
    print(" Git 저장소 정리 스크립트")
    print("=" * 70)
    print(f"작업 디렉토리: {BASE_DIR}")
    print()
    
    all_deleted = []
    
    # 1. 공통 불필요 파일 삭제
    print("🗑️  공통 불필요 파일 삭제 중...")
    for pattern in TO_DELETE:
        deleted = delete_pattern(BASE_DIR, pattern)
        all_deleted.extend(deleted)
        if deleted:
            print(f"  ✓ {pattern}: {len(deleted)}개 삭제")
    
    # 2. naver_blog 폴더 정리
    naver_deleted = cleanup_naver_blog()
    all_deleted.extend(naver_deleted)
    
    # 3. output 폴더 정리 (데이터 파일만 삭제, .gitkeep 유지)
    print("\n📊 output 폴더 정리 중...")
    output_dir = BASE_DIR / 'naver_blog' / 'output'
    if output_dir.exists():
        for item in output_dir.iterdir():
            if item.name != '.gitkeep':
                try:
                    if item.is_file():
                        item.unlink()
                        all_deleted.append(f"naver_blog/output/{item.name}")
                        print(f"  ✓ 삭제: {item.name}")
                except Exception as e:
                    print(f"  ⚠ 삭제 실패: {item.name} - {e}")
    
    # 4. 최종 요약
    print("\n" + "=" * 70)
    print(" 정리 완료!")
    print("=" * 70)
    print(f"총 {len(all_deleted)}개 파일/폴더 삭제됨")
    
    # 5. 남은 핵심 파일 확인
    print("\n✅ 유지된 핵심 파일:")
    naver_blog_dir = BASE_DIR / 'naver_blog'
    for keep_file in KEEP_FILES:
        file_path = naver_blog_dir / keep_file
        if file_path.exists():
            size = file_path.stat().st_size / 1024  # KB
            print(f"  • {keep_file} ({size:.1f} KB)")
    
    print("\n💡 다음 단계:")
    print("  1. git status 로 변경사항 확인")
    print("  2. git add . 로 파일 추가")
    print("  3. git commit -m 'Initial commit: Clean project structure'")
    print("  4. git push origin main")
    print("=" * 70)


if __name__ == "__main__":
    # 사용자 확인
    print("\n⚠️  경고: 이 스크립트는 파일을 영구적으로 삭제합니다!")
    print("계속하시겠습니까? (y/N): ", end="")
    
    response = input().strip().lower()
    if response == 'y':
        main()
    else:
        print("취소되었습니다.")
