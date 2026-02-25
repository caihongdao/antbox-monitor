#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞牛 OS 照片/视频去重工具
检测并删除 /vol3/1000/magic6 手机备份 目录下的重复文件
"""

import paramiko
import hashlib
import os
import sys
from datetime import datetime
from collections import defaultdict
from pathlib import PurePosixPath

# ============== 配置 ==============
FN_HOST = "192.168.12.200"
FN_USER = "caihong"
FN_PASS = "Www199054@@"
REMOTE_PATH = "/vol3/1000/magic6*"
LOCAL_LOG_DIR = "/tmp/fn_dedup_logs"

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.heif'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.m4v'}

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def print_progress(current, total, prefix='Progress', length=50):
    percent = float(current) / max(total, 1)
    arrow = '#' * int(round(percent * length) - 1) + '>'
    spaces = ' ' * (length - len(arrow))
    sys.stdout.write(f'\r{prefix}: [{arrow}{spaces}] {current}/{total} ({percent*100:.1f}%)')
    sys.stdout.flush()
    if current >= total:
        print()

def calculate_md5(filename):
    hash_md5 = hashlib.md5()
    try:
        cmd = f"md5sum '{filename}' 2>/dev/null"
        stdin, stdout, stderr = ssh_client.exec_command(cmd)
        result = stdout.read().decode('utf-8').strip()
        if result:
            return result.split()[0]
    except Exception as e:
        pass
    return None

def scan_files(base_path):
    files = []
    # Use simple shell command
    cmd = "/bin/bash -c \"find " + base_path + " -type f \\( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.gif' -o -iname '*.bmp' -o -iname '*.webp' -o -iname '*.mp4' -o -iname '*.mov' -o -iname '*.avi' -o -iname '*.mkv' -o -iname '*.mp4' \\) -printf '%s %T@ %p\\n' 2>/dev/null\""
    
    print(f"Scanning directory: {base_path}")
    try:
        stdin, stdout, stderr = ssh_client.exec_command(cmd)
        lines = stdout.readlines()
        total = len(lines)
        
        for i, line in enumerate(lines):
            parts = line.strip().split(' ', 2)
            if len(parts) >= 3:
                size = int(parts[0])
                mtime = datetime.fromtimestamp(float(parts[1]))
                path = parts[2]
                filename = path.split('/')[-1]
                ext = PurePosixPath(filename).suffix.lower()
                
                files.append({
                    'path': path,
                    'filename': filename,
                    'size': size,
                    'mtime': mtime,
                    'ext': ext
                })
            
            if (i + 1) % 1000 == 0:
                print_progress(i + 1, total, 'Scanning')
        
        print_progress(total, total, 'Scanning')
        
    except Exception as e:
        print(f"Scan failed: {str(e)}")
    
    return files

def find_duplicates(files):
    print_header("Step 2: Calculate file hashes")
    
    size_groups = defaultdict(list)
    for file in files:
        size_groups[file['size']].append(file)
    
    potential_duplicates = []
    for size, group in size_groups.items():
        if len(group) > 1:
            potential_duplicates.extend(group)
    
    print(f"Found {len(potential_duplicates)} files with potential duplicates (by size)")
    
    hash_groups = defaultdict(list)
    for i, file in enumerate(potential_duplicates):
        print_progress(i + 1, len(potential_duplicates), 'Calculating MD5')
        
        md5_hash = calculate_md5(file['path'])
        if md5_hash:
            file['md5'] = md5_hash
            hash_groups[md5_hash].append(file)
    
    duplicates = {hash_val: files for hash_val, files in hash_groups.items() if len(files) > 1}
    
    return duplicates

def select_files_to_delete(duplicate_files):
    files_to_delete = []
    
    for md5_hash, files in duplicate_files.items():
        sorted_files = sorted(files, key=lambda x: x['mtime'])
        keep_file = sorted_files[0]
        delete_files = sorted_files[1:]
        
        for file in delete_files:
            file['reason'] = f"Duplicate, keeping: {keep_file['path']}"
            file['keep_file'] = keep_file['path']
            files_to_delete.append(file)
    
    return files_to_delete

def delete_files(files_to_delete, dry_run=True):
    if not files_to_delete:
        print("No files to delete")
        return
    
    action = "[DRY RUN]" if dry_run else "[DELETING]"
    print_header(f"{action} Delete duplicate files")
    
    deleted_count = 0
    freed_space = 0
    
    for i, file in enumerate(files_to_delete, 1):
        try:
            size_mb = file['size'] / (1024 * 1024)
            if dry_run:
                print(f"{i}. Will delete: {file['path']}")
                print(f"   Size: {size_mb:.2f} MB, Time: {file['mtime']}")
                print(f"   Keep: {file['keep_file']}")
                print()
            else:
                stdin, stdout, stderr = ssh_client.exec_command(f"rm -f '{file['path']}'")
                error = stderr.read().decode('utf-8')
                if error:
                    print(f"Delete failed: {file['path']} - {error}")
                else:
                    print(f"Deleted: {file['path']} ({size_mb:.2f} MB)")
                    deleted_count += 1
                    freed_space += file['size']
        except Exception as e:
            print(f"Error: {file['path']} - {str(e)}")
    
    total_size = sum(f['size'] for f in files_to_delete)
    print_header("Statistics")
    print(f"Total duplicate files: {len(files_to_delete)}")
    print(f"Space to free: {total_size / (1024*1024):.2f} MB")
    
    if not dry_run:
        print(f"Actually deleted: {deleted_count} files")
        print(f"Freed space: {freed_space / (1024*1024):.2f} MB")

def save_report(duplicates, files_to_delete):
    os.makedirs(LOCAL_LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"{LOCAL_LOG_DIR}/dedup_report_{timestamp}.txt"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"FNOS Photo Deduplication Report\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Scanned: {REMOTE_PATH}\n\n")
        f.write(f"Duplicate groups: {len(duplicates)}\n")
        f.write(f"Duplicate files: {len(files_to_delete)}\n")
        f.write(f"Space to free: {sum(f['size'] for f in files_to_delete) / (1024*1024):.2f} MB\n\n")
        
        for md5_hash, files in duplicates.items():
            f.write(f"MD5: {md5_hash}\n")
            f.write(f"Files: {len(files)}\n")
            for file in files:
                f.write(f"  - {file['path']} ({file['size']/1024/1024:.2f} MB, {file['mtime']})\n")
            f.write("\n")
    
    print(f"Report saved: {report_path}")

def main():
    global ssh_client
    
    print_header("FNOS Photo/Video Deduplication Tool")
    
    print("Connecting to FNOS...")
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(
            hostname=FN_HOST,
            username=FN_USER,
            password=FN_PASS,
            timeout=10
        )
        print(f"Connected to {FN_HOST}")
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        sys.exit(1)
    
    global REMOTE_PATH
    
    try:
        stdin, stdout, stderr = ssh_client.exec_command("/bin/bash -c 'ls -d " + REMOTE_PATH + "'")
        result = stdout.read().decode('utf-8').strip()
        
        if result:
            actual_path = result.split('\n')[0]
            print(f"Directory exists: {actual_path}")
            REMOTE_PATH = actual_path
        else:
            print(f"Directory not found: {REMOTE_PATH}")
            sys.exit(1)
    except Exception as e:
        print(f"Check directory failed: {str(e)}")
        sys.exit(1)
    
    print_header("Step 1: Scan photo and video files")
    files = scan_files(REMOTE_PATH)
    print(f"\nScanned {len(files)} files")
    
    if not files:
        print("No files found")
        ssh_client.close()
        sys.exit(0)
    
    duplicates = find_duplicates(files)
    
    if not duplicates:
        print_header("Result")
        print("No duplicate files found!")
        save_report(duplicates, [])
        ssh_client.close()
        sys.exit(0)
    
    print(f"\nFound {len(duplicates)} duplicate groups")
    total_duplicates = sum(len(files) - 1 for files in duplicates.values())
    total_space = sum(sum(f['size'] for f in files[1:]) for files in duplicates.values())
    print(f"Duplicate files: {total_duplicates}")
    print(f"Space to free: {total_space / (1024*1024):.2f} MB")
    
    files_to_delete = select_files_to_delete(duplicates)
    delete_files(files_to_delete, dry_run=True)
    
    print_header("Confirm")
    response = input("Delete these duplicate files? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\nWARNING: This action cannot be undone!")
        confirm = input("Type 'YES' to confirm: ").strip()
        if confirm == 'YES':
            delete_files(files_to_delete, dry_run=False)
            save_report(duplicates, files_to_delete)
        else:
            print("Cancelled")
    else:
        print("Cancelled")
        save_report(duplicates, files_to_delete)
    
    ssh_client.close()
    print_header("Complete")

if __name__ == "__main__":
    main()
