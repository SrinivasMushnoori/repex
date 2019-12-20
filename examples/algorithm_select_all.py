

# ------------------------------------------------------------------------------
#
def select_replicas_all(waitlist, criteria, replica):
    '''
    once enough replicas are waiting, they are *all* up for exchange
    '''

    try:
        # check if size of wait list suffices (otherwise go to `except`)
        assert(len(waitlist) >= criteria['exchange_size'])

        # we have enough replicas.  Consider all to be exchange candidates and
        # return them, along with a new empty waitlist
        return [r for r in waitlist], []


    except Exception:

        # on failure, return the unchanged waitlist and an empty selection
        return [], waitlist


# ------------------------------------------------------------------------------

