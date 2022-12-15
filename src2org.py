#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import logging
import argparse
from itertools import chain


logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser(prog='src2org', description='Convert source code to org-file')
parser.add_argument('path', help='Path to sourse code')
parser.add_argument('-o', '--output', default='a.org', help='Output file name, default a.org')
parser.add_argument('-t', '--title', help='Org file title')

org_headers = [
    '# -*- coding: utf-8; mode: org -*-',
    '#+startup: fold'
]
src_file_langs = {
    '.py': 'python',
    '.txt': 'text',
    '.c': 'C',
    '.h': 'C',
    '.cpp': 'C++',
    '.hpp': 'C++',
    '.html': 'html',
    '.css': 'css',
    '.js': 'js',
    '.ini': 'conf'
}


def write_headers(path, outfile, config={}):
    logging.info('Write org-mode headers')
    path = os.path.dirname(path) if path.endswith('/') else path
    base_name = os.path.basename(path)
    print('\n'.join(org_headers), file=outfile)
    print(f'#+title: {config.get("title", base_name)}', file=outfile)
    print('\n', file=outfile)

def convert_file(file_name, outfile, context={}):
    logging.info(f'Convert file: {file_name}')
    base_file_name = os.path.basename(file_name)
    file_ext = os.path.splitext(file_name)[1].lower()
    if file_ext not in src_file_langs:
        logging.warning(f'Warning: unsupported file extension {file_name}')
        return
    with open(file_name) as srcfile:
        src_block_header = [
            f'#+begin_src {src_file_langs[file_ext]} :tangle {os.path.join(context.get("path", ""), base_file_name)}',
        ]
        if context.get('level', 1) > 1:
            src_block_header.append(':mkdirp yes')
        print('*' * context.get('level', 1), base_file_name, file=outfile)
        print(' '.join(src_block_header), file=outfile)
        print(srcfile.read(), file=outfile)
        print('#+end_src\n', file=outfile)

def convert_dir(path, outfile, white_list, context={}):
    if not len([path_ for path_ in white_list if path_.startswith(path)]):
        logging.warning(f'Skip directory: {path}')
        return
    logging.info(f'Convert directory: {path}')
    dir_name = os.path.dirname(path) if path.endswith('/') else path
    base_dir_name = os.path.basename(dir_name)
    print('*' * context.get('level', 1), f'{base_dir_name}/', file=outfile)
    entries = tuple(os.scandir(path))
    dirs = list(filter(lambda e: e.is_dir(), entries))
    dirs.sort(key=lambda e: e.name)
    files = list(filter(lambda e: e.is_file(), entries))
    files.sort(key=lambda e: e.name)
    for entry in chain(dirs, files):
        ctx = context.copy()
        ctx['path'] = os.path.join(ctx.get('path', ''), base_dir_name)
        ctx['level'] = ctx.get('level', 1) + 1
        if entry.is_dir():
            convert_dir(entry.path, outfile, white_list, ctx)
        elif entry.is_file():
            convert_file(entry.path, outfile, ctx)
        else:
            logging.error(f'Error: wrong path {entry.path}')

def convert(path, outfile_name, config={}):
    with open(outfile_name, 'w') as outfile:
        if os.path.isdir(path):
            write_headers(path, outfile, config)
            white_list = [path for path, dirs, files in os.walk(path) if len(files)]
            convert_dir(path, outfile, white_list)
        elif os.path.isfile(path):
            write_headers(path, outfile, config)
            convert_file(path, outfile)
        else:
            logging.error(f'Error: wrong path "{path}"')
            sys.exit()


if __name__ == '__main__':
    parsed_args = parser.parse_args()
    config = {}
    if parsed_args.title:
        config['title'] = parsed_args.title
    convert(parsed_args.path, parsed_args.output, config)
