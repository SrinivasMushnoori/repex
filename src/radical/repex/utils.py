
import radical.utils as ru


# ------------------------------------------------------------------------------
#
def expand_ln(to_link, src_sbox, tgt_sbox, rid, cycle, task_id=None):

    expand = {'rid'  : rid,
              'cycle': cycle}

    if not src_sbox: src_sbox = '.'
    if not tgt_sbox: tgt_sbox = '.'

    ret = list()
    for data in ru.as_list(to_link):
        src, tgt = data.split('>')
        try:
            src = src.strip() % expand
            tgt = tgt.strip() % expand
        except Exception as e:
            raise RuntimeError('expansion error: %s : %s : %s'
                              % (src, tgt, expand))
        # if task_id is None:
        #     ret.append('%s/%s > %s/%s_%s'
        #               % (src_sbox, src, tgt_sbox, tgt, task_id))
        # else:
        #
        ret.append('%s/%s > %s/%s' % (src_sbox, src, tgt_sbox, tgt))

    return ret


# ------------------------------------------------------------------------------
#
def last_task(replica):

    cs = replica.current_stage

    if cs >= len(replica.stages):
        cs -= 1

    assert(cs < len(replica.stages))
    tasks = replica.stages[cs].tasks

    assert(tasks)
    assert(len(tasks) == 1)

    return list(tasks)[0]


# ------------------------------------------------------------------------------

