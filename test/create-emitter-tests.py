import sys
import yaml
import hashlib

NS = 'Emitter'
EVENT_COUNT = 5

def encode_stream(line):
    for c in line:
        if c == '\n':
            yield '\\n'
        elif c == '"':
            yield '\\"'
        elif c == '\t':
            yield '\\t'
        elif ord(c) < 0x20:
            yield '\\x' + hex(ord(c))
        else:
            yield c

def encode(line):
    return ''.join(encode_stream(line))

def doc_start(implicit=False):
    if implicit:
        return {'emit': '', 'handle': 'DOC_START()'}
    else:
        return {'emit': 'YAML::DocStart', 'handle': 'DOC_START()'}

def doc_end(implicit=False):
    if implicit:
        return {'emit': '', 'handle': 'DOC_END()'}
    else:
        return {'emit': 'YAML::DocEnd', 'handle': 'DOC_END()'}

def scalar(value, tag='', anchor='', anchor_id=0):
    emit = []
    if tag:
        emit += ['YAML::VerbatimTag("%s")' % encode(tag)]
    if anchor:
        emit += ['YAML::Anchor("%s")' % encode(anchor)]
    emit += ['"%s"' % encode(value)]
    return {'emit': emit, 'handle': 'SCALAR("%s", %s, "%s")' % (encode(tag), anchor_id, encode(value))}

def gen_outlines():
    yield [doc_start(), scalar('foo\n'), doc_end()]
    yield [doc_start(True), scalar('foo\n'), doc_end()]
    yield [doc_start(), scalar('foo\n'), doc_end(True)]
    yield [doc_start(True), scalar('foo\n'), doc_end(True)]

def gen_events():
    for events in gen_outlines():
        yield events

def gen_tests():
    for events in gen_events():
        name = 'test' + hashlib.sha1(''.join(yaml.dump(event) for event in events)).hexdigest()[:20]
        yield {'name': name, 'events': events}
        

def create_emitter_tests(out):
    out.write('namespace %s {\n' % NS)

    for test in gen_tests():
        out.write('inline TEST %s(YAML::Emitter& out)\n' % test['name'])
        out.write('{\n')
        for event in test['events']:
            emit = event['emit']
            if isinstance(emit, list):
                for e in emit:
                    out.write('    out << %s;\n' % e)
            elif emit:
                out.write('    out << %s;\n' % emit)
        out.write('\n')
        out.write('    HANDLE(out.c_str());\n')
        for event in test['events']:
            handle = event['handle']
            if handle:
                out.write('    EXPECT_%s;\n' % handle)
        out.write('    DONE();\n')
        out.write('}\n')

    out.write('}\n')

if __name__ == '__main__':
    create_emitter_tests(sys.stdout)