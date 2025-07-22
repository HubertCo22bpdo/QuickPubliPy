# From : https://gist.github.com/brews/8d3b3ede15d120a86a6bd6fc43859c5e
# by Brewster (brews) Malevich https://orcid.org/0000-0002-4752-8190

import requests
import json


def fetchmeta(doi, fmt='dict', **kwargs):
    """Fetch metadata for a given DOI.

    Parameters
    ----------
    doi : str
    fmt : str, optional
        Desired metadata format. Can be 'dict' or 'bibtex'.
        Default is 'dict'.
    **kwargs :
        Additional keyword arguments are passed to `json.loads()` if `fmt`
        is 'dict' and you're a big JSON nerd.

    Returns
    -------
    out : str or dict or None
        `None` is returned if the server gives unhappy response. Usually 
        this means the DOI is bad.

    Examples
    --------
    >>> fetchmeta('10.1016/j.dendro.2018.02.005')
    >>> fetchmeta('10.1016/j.dendro.2018.02.005', 'bibtex')
    
    References
    ----------
    https://www.doi.org/hb.html
    """
    # Parse args and setup the server response we want.
    accept_type = 'application/'
    if fmt == 'dict':
        accept_type += 'citeproc+json'
    elif fmt == 'bibtex':
        accept_type += 'x-bibtex'
    else:
        raise ValueError("`fmt` must be 'dict' or 'bibtex'")

    # Request data from server.
    url = "https://dx.doi.org/" + str(doi)
    header = {'accept': accept_type}
    r = requests.get(url, headers=header)

    # Format metadata if server response is good.
    out = None
    if r.status_code == 200 and fmt == 'dict':
        out = json.loads(r.text, **kwargs)
    elif r.status_code == 200 and fmt == 'bibtex':
        out = r.text

    return out
