import math
import numpy as np

from synsemnet.util import stderr


def get_char_set(text):
    charset = set()
    for s in text:
        for w in s:
            for c in w:
                charset.add(c)
    return [''] + sorted(list(charset))


def get_vocabulary(text):
    vocab = set()
    for s in text:
        for w in s:
            vocab.add(w)
    return [''] + sorted(list(vocab))


def get_pos_label_set(pos_labels):
    pos_label_set = set()
    for s in pos_labels:
        for p in s:
            pos_label_set.add(p)
    return sorted(list(pos_label_set))


def get_parse_label_set(parse_labels):
    parse_label_set = set()
    for s in parse_labels:
        for l in s:
            parse_label_set.add(l)
    return sorted(list(parse_label_set))


def get_parse_ancestor_set(parse_labels):
    parse_ancestor_set = set()
    for s in parse_labels:
        for l in s:
            parse_ancestor_set.add(l.split('_')[-1])
    return sorted(list(parse_ancestor_set))


def get_random_permutation(n):
    p = np.random.permutation(np.arange(n))
    p_inv = np.zeros_like(p)
    p_inv[p] = np.arange(n)
    return p, p_inv


def pad_sequence(x, out=None, seq_shape=None, cur_ix=None, dtype='float32', reverse_axes=None, padding='pre', value=0.):
    assert padding.lower() in ['pre', 'post'], 'Padding type "%s" not recognized' % padding
    if seq_shape is None:
        seq_shape = shape(x)

    if out is None:
        out = np.full(seq_shape, value, dtype=dtype)

    if cur_ix is None:
        cur_ix = []

    if reverse_axes is None:
        reverse_axes = tuple()
    elif reverse_axes is True:
        reverse_axes = tuple(range(len(seq_shape)))
    elif not isinstance(reverse_axes, list):
        reverse_axes = tuple(reverse_axes)

    reverse = len(cur_ix) in reverse_axes

    if hasattr(x, '__getitem__'):
        if padding.lower() == 'post':
            s = 0
            e = len(x)
        else:
            e = seq_shape[len(cur_ix)]
            s = e - len(x)
        for i, y in enumerate(x):
            if reverse:
                ix = cur_ix + [e - 1 - i]
            else:
                ix = cur_ix + [s + i]
            pad_sequence(
                y,
                out=out,
                seq_shape=seq_shape,
                cur_ix=ix,
                dtype=dtype,
                reverse_axes=reverse_axes,
                padding=padding,
                value=value
            )
    else:
        out[tuple(cur_ix)] = x

    return out


def rank(seqs):
    r = 0
    new_r = r
    if hasattr(seqs, '__getitem__'):
        r += 1
        for s in seqs:
            new_r = max(new_r, r + rank(s))
    return new_r


def shape(seqs, s=None, rank=0):
    if s is None:
        s = []
    if hasattr(seqs, '__getitem__'):
        if len(s) <= rank:
            s.append(len(seqs))
        s[rank] = max(s[rank], len(seqs))
        for c in seqs:
            s = shape(c, s=s, rank=rank+1)
    return s


def read_parse_label_file(path):
    text = []
    pos_label = []
    parse_label = []
    text_cur = []
    pos_label_cur = []
    parse_label_cur = []
    with open(path, 'r') as f:
        for l in f:
            if l.strip() == '':
                assert len(text_cur) == len(pos_label_cur) == len(parse_label_cur), 'Mismatched text and labels: [%s] vs. [%s] vs. [%s].' % (' '.join(text_cur), ' '.join(pos_label_cur), ' '.join(parse_label_cur))
                text.append(text_cur)
                pos_label.append(pos_label_cur)
                parse_label.append(parse_label_cur)
                text_cur = []
                pos_label_cur = []
                parse_label_cur = []
            else:
                w, p, l = l.strip().split()
                text_cur.append(w)
                pos_label_cur.append(p)
                parse_label_cur.append(l)

    return text, pos_label, parse_label


# TODO: For Evan
def read_sts_file(path):
    sts_s1_text = []
    sts_s1_text = []
    sts_label = []

    # COMPUTE THESE FROM FILE AT PATH

    return sts_s1_text, sts_s1_text, sts_label

def print_interlinearized(lines, max_tokens=20):
    out = []
    for l1 in zip(*lines):
        out.append([])
        n_tok = 0
        for w in zip(*l1):
            if n_tok == max_tokens:
                out[-1].append([[] for _ in range(len(w))])
                n_tok = 0
            if len(out[-1]) == 0:
                out[-1].append([[] for _ in range(len(w))])
            max_len = max([len(x) for x in w])
            for i, x in enumerate(w):
                out[-1][-1][i].append(x + ' ' * (max_len - len(x)))
            n_tok += 1

    string = ''
    for l1 in out:
        for l2 in l1:
            for x in l2:
                string += ' '.join(x) + '\n'
        string += '\n'

    return string


class Dataset(object):
    def __init__(
            self,
            parsing_train_path,
            sts_train_path
    ):
        self.files = {}

        self.initialize_parsing_file(parsing_train_path, 'train')

        parsing_text = self.files['train']['parsing_text_src']
        pos_label = self.files['train']['pos_label_src']
        parse_label = self.files['train']['parse_label_src']

        self.initialize_sts_file(sts_train_path, 'train')
        sts_s1_text = self.files['train']['sts_s1_text_src']
        sts_s2_text = self.files['train']['sts_s2_text_src']
        sts_label = self.files['train']['sts_label_src']

        texts = parsing_text + sts_s1_text + sts_s2_text

        self.char_list = get_char_set(texts)
        self.word_list = get_vocabulary(texts)
        self.pos_label_list = get_pos_label_set(pos_label)
        self.parse_label_list = get_parse_label_set(parse_label)
        self.parse_ancestor_list = get_parse_ancestor_set(parse_label)

        self.char_map = {c: i for i, c in enumerate(self.char_list)}
        self.word_map = {w: i for i, w in enumerate(self.word_list)}
        self.pos_label_map = {p: i for i, p in enumerate(self.pos_label_list)}
        self.parse_label_map = {l: i for i, l in enumerate(self.parse_label_list)}
        self.parse_ancestor_map = {l: i for i, l in enumerate(self.parse_ancestor_list)}

        self.n_char = len(self.char_map)
        self.n_word = len(self.word_map)
        self.n_pos = len(self.pos_label_map)
        self.n_parse_label = len(self.parse_label_map)
        self.n_parse_ancestor = len(self.parse_ancestor_map)

    def initialize_parsing_file(self, path, name):
        text, pos_label, parse_label = read_parse_label_file(path)

        new = {
            'parsing_text_src': text,
            'pos_label_src': pos_label,
            'parse_label_src': parse_label
        }

        self.files[name] = new

    def initialize_sts_file(self, path, name):
        sts_s1_text, sts_s2_text, sts_label = read_sts_file(path)

        new = {
            'sts_s1_text_src': sts_s1_text,
            'sts_s2_text_src': sts_s2_text,
            'sts_label_src': sts_label
        }

        self.files[name] = new

    def cache_numeric_parsing_data(self, name='train', factor_parse_labels=True):
        self.files[name]['parsing_text'], self.files[name]['parsing_text_mask'] = self.symbols_to_padded_seqs(
            name=name,
            data_type='parsing_text',
            return_mask=True
        )
        self.files[name]['pos_label'] = self.symbols_to_padded_seqs(name=name, data_type='pos_label')
        if factor_parse_labels:
            self.files[name]['parse_depth'] = self.symbols_to_padded_seqs(name=name, data_type='parse_depth')
            self.files[name]['parse_label'] = self.symbols_to_padded_seqs(name=name, data_type='parse_ancestor')
        else:
            self.files[name]['parse_depth'] = None
            self.files[name]['parse_label'] = self.symbols_to_padded_seqs(name=name, data_type='parse_label')

    # TODO: For Evan
    def cache_numeric_sts_data(self, name='train', factor_parse_labels=True):
        return

    def get_seqs(self, name='train', data_type='parsing_text_src', as_words=True):
        data = self.files[name][data_type]

        if as_words:
            return data
        else:
            text = []
            for s in data:
                text.append(' '.join(s))
            return text

    def char_to_int(self, c):
        return self.char_map.get(c, 0)

    def int_to_char(self, i):
        return self.char_list[i]

    def word_to_int(self, w):
        return self.word_map.get(w, 0)

    def int_to_word(self, i):
        return self.word_list[i]

    def pos_label_to_int(self, p):
        return self.pos_label_map[p]

    def int_to_pos_label(self, i):
        return self.pos_label_list[i]

    def parse_label_to_int(self, l):
        return self.parse_label_map[l]

    def int_to_parse_label(self, i):
        return self.parse_label_list[i]

    def parse_ancestor_to_int(self, a):
        return self.parse_ancestor_map[a.split('_')[-1]]

    def int_to_parse_ancestor(self, i):
        return self.parse_ancestor_list[i]

    def parse_depth_to_int(self, d):
        return 0 if d in ['NONE', '-BOS-', '-EOS-'] else int(d.split('_')[0])

    def int_to_parse_depth(self, i):
        return str(i)

    def ints_to_parse_joint_depth_on_all(self, i_depth, i_ancestor):
        depth = self.int_to_parse_depth(i_depth)
        ancestor = self.int_to_parse_ancestor(i_ancestor)
        return '_'.join([depth, ancestor])

    def ints_to_parse_joint(self, i_depth, i_ancestor):
        depth = self.int_to_parse_depth(i_depth)
        ancestor = self.int_to_parse_ancestor(i_ancestor)
        return ancestor if ancestor in ['None', '-BOS-', '-EOS-'] else '_'.join([depth, ancestor])

    def sts_label_to_int(self, i):
        return int(i)

    def int_to_sts_label(self, i):
        return str(i)

    def symbols_to_padded_seqs(
            self,
            name='train',
            data_type='parsing_text',
            max_token=None,
            max_subtoken=None,
            as_char=False,
            word_tokenized=True,
            char_tokenized=True,
            return_mask=False
    ):
        data_type_tmp = data_type + '_src'
        if data_type.lower() in ['parsing_text', 'sts_s1_text', 'sts_s1_text']:
            if word_tokenized:
                if char_tokenized:
                    as_words = True
                    if as_char:
                        f = lambda x: [y[:max_subtoken] for y in x]
                    else:
                        f = lambda x: list(map(self.char_to_int, x[:max_subtoken]))
                else:
                    as_words = True
                    if as_char:
                        f = lambda x: x
                    else:
                        f = self.word_to_int
            else:
                if char_tokenized:
                    as_words = False
                    if as_char:
                        f = lambda x: x
                    else:
                        f = self.char_to_int
                else:
                    raise ValueError('Text must be tokenized at the word or character level (or both).')
        elif data_type.lower() == 'pos_label':
            as_words = True
            if as_char:
                f = lambda x: x
            else:
                f = self.pos_label_to_int
        elif data_type.lower() == 'parse_label':
            as_words = True
            if as_char:
                f = lambda x: x
            else:
                f = self.parse_label_to_int
        elif data_type.lower() == 'parse_depth':
            as_words = True
            data_type_tmp = 'parse_label_src'
            if as_char:
                f = lambda x: x if x in ['NONE', '-BOS-', '-EOS-'] else x.split('_')[0]
            else:
                f = self.parse_depth_to_int
        elif data_type.lower() == 'parse_ancestor':
            as_words = True
            data_type_tmp = 'parse_label_src'
            if as_char:
                f = lambda x: x.split('_')[-1]
            else:
                f = self.parse_ancestor_to_int
        elif data_type.lower() == 'sts_label':
            # TODO: For Evan
            pass
        else:
            raise ValueError('Unrecognized data_type "%s".' % data_type)

        data = self.get_seqs(name=name, data_type=data_type_tmp, as_words=as_words)

        out = []
        if return_mask:
            mask = []
        for i, s in enumerate(data):
            newline = list(map(f, s))[:max_token]
            out.append(newline)
            if return_mask:
                if data_type.endswith('text') and char_tokenized and word_tokenized:
                    mask.append([[1] * len(x) for x in newline])
                else:
                    mask.append([1] * len(newline))

        out = pad_sequence(out, value=0)
        if not as_char:
            out = out.astype('int')
        if data_type.lower().endswith('parse_depth'):
            final_depth = -out[..., :-1].sum(axis=-1)
            out[..., -1] = final_depth
        if return_mask:
            mask = pad_sequence(mask)

        if return_mask:
            return out, mask

        return out

    def padded_seqs_to_symbols(
            self,
            data,
            data_type,
            mask=None,
            as_list=True,
            depth_on_all=True,
            char_tokenized=True,
            word_tokenized=True
    ):
        if data_type.lower().endswith('text'):
            if char_tokenized:
                f = np.vectorize(self.int_to_char, otypes=[np.str])
            else:
                if word_tokenized:
                    f = np.vectorize(self.int_to_word, otypes=[np.str])
                else:
                    raise ValueError('Text must be tokenized at the word or character level (or both).')
        elif data_type.lower() == 'pos_label':
            f = np.vectorize(self.int_to_pos_label, otypes=[np.str])
        elif data_type.lower() == 'parse_label':
            f = np.vectorize(self.int_to_parse_label, otypes=[np.str])
        elif data_type.lower() == 'parse_depth':
            f = np.vectorize(self.int_to_parse_depth, otypes=[np.str])
        elif data_type.lower() == 'parse_ancestor':
            f = np.vectorize(self.int_to_parse_ancestor, otypes=[np.str])
        elif data_type.lower() == 'parse_joint':
            if depth_on_all:
                f = np.vectorize(self.ints_to_parse_joint_depth_on_all, otypes=[np.str])
            else:
                f = np.vectorize(self.ints_to_parse_joint, otypes=[np.str])
        elif data_type.lower() == 'sts_label':
            # TODO: For Evan
            pass
        else:
            raise ValueError('Unrecognized data_type "%s".' % data_type)

        if data_type.lower() == 'parse_joint':
            data = f(*data)
        else:
            data = f(data)
        if mask is not None:
            data = np.where(mask, data, np.zeros_like(data).astype('str'))
        data = data.tolist()
        out = []
        for s in data:
            newline = []
            for w in s:
                if data_type.endswith('text') and char_tokenized and word_tokenized:
                    w = ''.join(w)
                if w != '':
                    newline.append(w)
            if as_list:
                s = newline
            else:
                s = ' '.join(newline)
            out.append(s)

        if not as_list:
            out = '\n'.join(out)

        return out

    def get_parsing_data_feed(
            self,
            name,
            minibatch_size=128,
            randomize=False
    ):
        parsing_text = self.files[name]['parsing_text']
        parsing_text_mask = self.files[name]['parsing_text_mask']
        pos_label = self.files[name]['pos_label']
        parse_label = self.files[name]['parse_label']
        parse_depth = self.files[name]['parse_depth']

        n = self.get_n(name)

        i = 0

        if randomize:
            ix, ix_inv = get_random_permutation(n)
        else:
            ix = np.arange(n)

        while i < n:
            indices = ix[i:i+minibatch_size]

            out = {
                'parsing_text': parsing_text[indices],
                'parsing_text_mask': parsing_text_mask[indices],
                'pos_label': pos_label[indices],
                'parse_label': parse_label[indices],
                'parse_depth': None if parse_depth is None else parse_depth[indices],
            }

            yield out

            i += minibatch_size

    def get_sts_data_feed(
            self,
            name,
            minibatch_size=128,
            randomize=False
    ):
        # TODO: For Evan
        pass

    def get_data_feed(
            self,
            name,
            parsing=True,
            sts=True,
            minibatch_size=128,
            randomize=False
    ):
        # TODO: Complete once STS data pipeline is finished
        pass

    def get_n(self, name):
        return len(self.files[name]['parsing_text'])

    def get_n_minibatch(self, name, minibatch_size):
        return math.ceil(self.get_n(name) / minibatch_size)

    def parse_predictions_to_sequences(self, numeric_chars, numeric_pos, numeric_label, numeric_depth=None, mask=None):
        if mask is not None:
            char_mask = mask
            word_mask = mask.any(axis=-1)
        else:
            char_mask = None
            word_mask = None

        words = self.padded_seqs_to_symbols(numeric_chars, 'parsing_text', mask=char_mask, as_list=True)
        pos = self.padded_seqs_to_symbols(numeric_pos, 'pos_label', mask=word_mask, as_list=True)
        if numeric_depth is None:
            label = self.padded_seqs_to_symbols(numeric_label, 'parse_label', mask=word_mask, as_list=True)
        else:
            label = self.padded_seqs_to_symbols([numeric_depth, numeric_label], 'parse_joint', mask=word_mask, as_list=True, depth_on_all=False)

        out = ''

        for s_w, s_p, s_l in zip(words, pos, label):
            for x in zip(s_w, s_p, s_l):
               out += '\t'.join(x) + '\n'
            out += '\n'

        return out

    def sts_predictions_to_sequences(self, *args, **kwargs):
        # TODO: For Evan
        pass

    def pretty_print_parse_predictions(
            self,
            text=None,
            pos_label_true=None,
            pos_label_pred=None,
            parse_label_true=None,
            parse_label_pred=None,
            parse_depth_true=None,
            parse_depth_pred=None,
            mask=None
    ):
        if mask is not None:
            char_mask = mask
            word_mask = mask.any(axis=-1)
        else:
            char_mask = None
            word_mask = None

        to_interlinearize = []

        if parse_depth_true is None:
            if parse_label_true is not None:
                parse_label_true = self.padded_seqs_to_symbols(parse_label_true, 'parse_label', mask=word_mask)
                to_interlinearize.append(parse_label_true)
        else:
            if parse_label_true is not None:
                parse_label_true = self.padded_seqs_to_symbols([parse_depth_true, parse_label_true], 'parse_joint', mask=word_mask)
                to_interlinearize.append(parse_label_true)
        if parse_depth_pred is None:
            if parse_label_pred is not None:
                parse_label_pred = self.padded_seqs_to_symbols(parse_label_pred, 'parse_label', mask=word_mask)
                to_interlinearize.append(parse_label_pred)
        else:
            if parse_label_pred is not None:
                parse_label_pred = self.padded_seqs_to_symbols([parse_depth_pred, parse_label_pred], 'parse_joint', mask=word_mask)
                to_interlinearize.append(parse_label_pred)
        if pos_label_true is not None:
            pos_label_true = self.padded_seqs_to_symbols(pos_label_true, 'pos_label', mask=word_mask)
            to_interlinearize.append(pos_label_true)
        if pos_label_pred is not None:
            pos_label_pred = self.padded_seqs_to_symbols(pos_label_pred, 'pos_label', mask=word_mask)
            to_interlinearize.append(pos_label_pred)
        if text is not None:
            text = self.padded_seqs_to_symbols(text, 'parsing_text', mask=char_mask)
            to_interlinearize.append(text)

        for i in range(len(text)):
            if parse_label_true is not None:
                parse_label_true[i] = ['Parse True:'] + parse_label_true[i]
            if parse_label_pred is not None:
                parse_label_pred[i] = ['Parse Pred:'] + parse_label_pred[i]
            if pos_label_true is not None:
                pos_label_true[i] = ['POS True:'] + pos_label_true[i]
            if pos_label_pred is not None:
                pos_label_pred[i] = ['POS Pred:'] + pos_label_pred[i]
            if text is not None:
                text[i] = ['Word:'] + text[i]

        return print_interlinearized(to_interlinearize)

    def pretty_print_sts_predictions(
            self,
            *args,
            **kwargs
    ):
        # TODO: For Evan
        pass









