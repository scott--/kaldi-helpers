#!/usr/bin/python3

# Given a json file with transcript information this tools can perform
# manipulations including generating word lists.
# Optionally provide the output json file name with -j
# Usage: python filter_text.py sample.json wordlist.txt


import argparse
import json
import re
import string
import sys


def save_wordlist(wordlist, filename):
    # Given a list of strings write to file
    try:
        with open(filename, 'w') as f:
            for word in wordlist:
                f.write(word + '\n')
    except Exception:
        print("Could not write out to file " + filename)
        exit()


def extract_wordlist(data):
    # Given the data object produce a list of strings of single words
    # Returned list is of unique words and sorted
    result = []
    for utt in data:
        words = utt.get('transcript').split()
        result.extend(words)
    result = list(set(result))
    result.sort()
    return result


def load_file(filename=""):
    # Given a filename load and return the object
    try:
        f = sys.stdin
        if filename:
            f = open(filename, "r", encoding="utf-8")
        data = json.load(f)
    except Exception as e:
        print("Could not read file " + filename)
        exit()
    return data


def write_json(data):
    # Write a data object in json format
    try:
        print(json.dumps(data, indent=2))
    except Exception:
        print("Could not write out json file")
        exit()


def filter_data(data, removeEng=False):

    # Given a data object remove any transcriptons with undesirable features
    to_remove = string.punctuation + "…’“–”‘°"
    # Any words you want to ignore
    special_cases = ["<silence>"]
    translation_tags = set(['@eng@', '<ind:', '<eng:'])
    cleaned_data = []

    if removeEng:
        use_langid = False
        if use_langid:
            from langid.langid import LanguageIdentifier, model
            identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        from nltk.corpus import words
        eng_words = set(words.words())
        # Using both 2.16% english in wordlist 14.6k words(slow)
        # Using nltk dictionary 2.49% englisb in wordlist 15.5k words (fast)
        # Using neither 11.1% english in wordlist 34.8k words (fast)
        # Only words > 3 chars are counted, for audio-segment sample
        # Using remove english and ignore after '<' 1.8% 20.4K

    for utt in data:
        # print(utt, file=sys.stderr)

        trans = utt.get('transcript').lower()
        words = trans.split()

        # Note this is an assumption only translations come after '<'
        # if "<" in trans:
        # r = re.search(r'[<]@?(eng|indo|ind|mala)', trans)
        # if bool(r):
        #     words = trans[:r.span()[0]].split()

        clean_words = []
        valid_utterance = True
        eng_count = 0
        for word in words:
            # If a special case ignore
            if word in special_cases:
                continue

            # If utterance contains a translation
            if word in translation_tags:  # Translations / ignore
                break

            # If partial digit, throw out whole utterance
            if bool(re.search(r'\d', word)) and not word.isdigit():
                valid_utterance = False
                break

            # Remove punctuation and bad chars
            for char in to_remove:
                word = word.replace(char, '')

            # If word is in english dictionary count it
            if removeEng and len(word) > 3 and word in eng_words:
                # print(word, file=sys.stderr)
                eng_count += 1

            clean_words.append(word)

        # Exclude utterance if empty after cleaning
        cleaned_trans = ' '.join(clean_words).strip()
        if cleaned_trans == "":
            valid_utterance = False

        # Exclude utterance if > 10% english
        if removeEng and len(clean_words) > 0 and eng_count / len(clean_words) > 0.1:
            # print(round(eng_count / len(clean_words)), trans, file=sys.stderr)
            valid_utterance = False

        # Exclude utterance if langid thinks its english
        if removeEng and use_langid and valid_utterance:
            lang, prob = identifier.classify(cleaned_trans)
            if lang == 'en' and prob > 0.5:
                valid_utterance = False

        # Something was bad in utterance
        if not valid_utterance:
            continue

        # Should be a clean valid utterance
        utt['transcript'] = cleaned_trans
        cleaned_data.append(utt)
    return cleaned_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", type=str, help="The input file to clean.")
    parser.add_argument("-re", "--removeEng", help="Remove english like utterances", action="store_true")
    args = parser.parse_args()

    data = load_file(args.infile)

    print("Filtering...", end='', flush=True, file=sys.stderr)

    f_data = filter_data(data, args.removeEng)  # mutates the data object

    write_json(f_data)
    # print(f_data, file=sys.stderr)
    # print("Done.", file=sys.stderr)


if __name__ == '__main__':
    main()
