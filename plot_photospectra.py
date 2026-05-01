import base64
import json
import math
from io import BytesIO

import matplotlib
import requests
from matplotlib.figure import Figure

matplotlib.use('Agg')

kwargs = None

INTERNAL_RELEASES = ('dr5', 'dr6')

BANDS = [
  'u', 'J0378', 'J0395', 'J0410', 'J0430', 'g', 'J0515', 'r', 'J0660', 'i',
  'J0861', 'z'
]

APERTURES = ['iso', 'aper_3', 'aper_6', 'auto', 'petro', 'pstotal']
APERTURES_DR6 = ['isophotal', 'aper_3', 'aper_6', 'auto', 'petro', 'pstotal']

def dr3_mapping():
  mags = {f'{band}_{aper}': f'mag_{band}_{aper}' for band in BANDS for aper in APERTURES}
  err = {f'e_{band}_{aper}': f'mag_err_{band}_{aper}' for band in BANDS for aper in APERTURES}
  return {**mags, **err}

def dr4_mapping():
  mags = {f'{band}.{band}_{aper}': f'mag_{band}_{aper}' for band in BANDS for aper in APERTURES}
  err = {f'{band}.e_{band}_{aper}': f'mag_err_{band}_{aper}' for band in BANDS for aper in APERTURES}
  return {**mags, **err}

def dr6_mapping():
  mags = {f'mag_{aper_dr6}_{band.lower()}': f'mag_{band}_{aper}' for band in BANDS for aper, aper_dr6 in zip(APERTURES, APERTURES_DR6)}
  err = {f'err_mag_{aper_dr6}_{band.lower()}': f'mag_err_{band}_{aper}' for band in BANDS for aper, aper_dr6 in zip(APERTURES, APERTURES_DR6)}
  return {**mags, **err}


MAPPING = {
  'dr3': dr3_mapping(),
  'dr4': dr4_mapping(),
  'dr5': dr3_mapping(),
  'dr6': dr6_mapping(),
}


def dr3_query(ra, dec, radius):
  return f"""
    SELECT TOP 1 {','.join([f't.{k} AS {v}' for k, v in MAPPING['dr3'].items()])},
      DISTANCE(POINT('ICRS', {ra}, {dec}), POINT('ICRS', t.ra, t.dec)) AS dist
    FROM dr3.all_dr3 AS t
    WHERE 1 = CONTAINS(POINT('ICRS', t.ra, t.dec), CIRCLE('ICRS', {ra}, {dec}, {radius}))
    ORDER BY dist ASC
  """

def dr4_query(ra, dec, radius):
  return f"""
    SELECT TOP 1 det.ra, det.dec, 
      {','.join([f'{k} AS {v}' for k, v in MAPPING['dr4'].items()])},
      DISTANCE(POINT('ICRS', {ra}, {dec}), POINT('ICRS', det.ra, det.dec)) AS dist
    FROM dr4_dual.dr4_dual_detection AS det JOIN
      dr4_dual.dr4_dual_g AS g on g.id = det.id JOIN
      dr4_dual.dr4_dual_z AS z on z.id = det.id JOIN
      dr4_dual.dr4_dual_r AS r on r.id = det.id JOIN
      dr4_dual.dr4_dual_i AS i on i.id = det.id JOIN
      dr4_dual.dr4_dual_u AS u on u.id = det.id JOIN
      dr4_dual.dr4_dual_j0378 AS J0378 on j0378.id = det.id JOIN
      dr4_dual.dr4_dual_j0395 AS J0395 on j0395.id = det.id JOIN
      dr4_dual.dr4_dual_j0410 AS J0410 on j0410.id = det.id JOIN
      dr4_dual.dr4_dual_j0430 AS J0430 on j0430.id = det.id JOIN
      dr4_dual.dr4_dual_j0515 AS J0515 on j0515.id = det.id JOIN
      dr4_dual.dr4_dual_j0660 AS J0660 on j0660.id = det.id JOIN
      dr4_dual.dr4_dual_j0861 AS J0861 on j0861.id = det.id 
    WHERE 1 = CONTAINS(POINT('ICRS', det.ra, det.dec), CIRCLE('ICRS', {ra}, {dec}, {radius}))
    ORDER BY dist ASC
  """

def dr5_query(ra, dec, radius):
  return f"""
    SELECT TOP 1 {','.join([f't.{k} AS {v}' for k, v in MAPPING['dr5'].items()])},
      DISTANCE(POINT('ICRS', {ra}, {dec}), POINT('ICRS', t.ra, t.dec)) AS dist
    FROM idr5.idr5_dual AS t
    WHERE 1 = CONTAINS(POINT('ICRS', t.ra, t.dec), CIRCLE('ICRS', {ra}, {dec}, {radius}))
    ORDER BY dist ASC
  """

def dr6_query(ra, dec, radius):
  return f"""
    SELECT TOP 1 {','.join([f't.{k} AS {v}' for k, v in MAPPING['dr6'].items()])},
      DISTANCE(POINT('ICRS', {ra}, {dec}), POINT('ICRS', t.ra, t.dec)) AS dist
    FROM idr6.idr6 AS t
    WHERE 1 = CONTAINS(POINT('ICRS', t.ra, t.dec), CIRCLE('ICRS', {ra}, {dec}, {radius}))
    ORDER BY dist ASC
  """

QUERIES = {
  'dr3': dr3_query,
  'dr4': dr4_query,
  'dr5': dr5_query,
  'dr6': dr6_query,
}




def fetch_photospectra(ra: float, dec: float, dr: str = 'dr6', token: str = None):
  data = {
    "query": QUERIES[dr](ra=ra, dec=dec, radius=0.0014),
    "mode": "adql",
    "format": "json"
  }

  headers = None
  if dr in (INTERNAL_RELEASES):
    headers = {
      "Authorization": f"Bearer {token}",
    }

  resp = requests.post("https://splus.cloud/adss/sync", data=data, headers=headers)
  
  try:
    return resp.json()
  except Exception:
    return None



def bytes_to_base64(buffer, fmt: str = 'jpeg'):
  buffer.seek(0)
  img_b64 = base64.b64encode(buffer.getvalue()).decode('utf8')
  return f'data:image/{fmt};base64,{img_b64}'



def plot_photospectra(
  ra: float, 
  dec: float, 
  dr: str = 'dr6',
  token: str = None,
  data: dict = None,
  **kwargs
):
  if data is None:
    data = fetch_photospectra(ra, dec, dr, token)
  
  if data is None:
    return None
  
  colors = ['tab:blue', 'tab:green', 'tab:red', 'tab:orange', 'tab:purple', 'tab:brown']
  x = [3485, 3785, 3950, 4100, 4300, 4803, 5150, 6250, 6600, 7660, 8610, 9110]

  def mask(v):
    return math.nan if v is None or v < 9 or v > 25 else v
  
  def error_mask(v): 
    return math.nan if v is None or v > 2 else v
  
  def nan_filter(x, y): 
    return zip(*filter(lambda _x: not math.isnan(_x[1]), zip(x, y)))
  
  y_min, y_max = 999999, -999999

  fig = Figure(figsize=(10, 7))
  ax = fig.subplots()
  plot_params = {
    'fmt': '-',
    'capsize': 4,
    'alpha': 0.95,
    'linewidth': 1,
    'markersize': 3,
    'marker': 'o'
  }
  
  for aperture, color in zip(APERTURES, colors):
    mag = [data[f'mag_{band.lower()}_{aperture}'] for band in BANDS]
    err = [data[f'mag_err_{band.lower()}_{aperture}'] for band in BANDS]
    
    filt_mag = list(map(mask, mag))
    filt_err = list(map(error_mask, err))
    filtered_x, filtered_y = nan_filter(x, filt_mag)
    y_min = min(y_min, *filtered_y)
    y_max = max(y_max, *filtered_y)
    ax.plot(filtered_x, filtered_y, '--', color=color, alpha=0.75, linewidth=0.8)
    ax.errorbar(x, filt_mag, yerr=filt_err, label=aperture, color=color, **plot_params)

  ax.set_xlabel('Wavelength [$\\AA$]')
  ax.set_ylabel('Magnitude (AB)')
  ax.set_title(f'S-PLUS photo-spectrum (RA: {float(ra):.4f} DEC: {float(dec):.4f})')
  ax.set_ylim(y_min - 0.18, y_max + 0.18)
  ax.minorticks_on()
  ax.tick_params(axis='both', which='both', direction='in', right=True)
  ax.grid(True, which='major', axis='y', alpha=0.6, linestyle=':')
  ax.invert_yaxis()
  ax.legend()

  bands_ax = ax.twiny()
  bands_ax.set_xlim(ax.get_xlim())
  bands_ax.set_xticks(x)
  bands_ax.set_xticklabels(
    BANDS,
    ha='left',
    va='center',
    rotation=65,
    rotation_mode='anchor'
  )
  bands_ax.tick_params(axis='both', direction='in')
  bands_ax.grid(True, which='major', axis='x', alpha=0.6, linestyle=':')
  
  buff = BytesIO()
  fig.savefig(buff, format='jpg', bbox_inches='tight', pad_inches=0.1)
  res = bytes_to_base64(buff)
  fig.clear()
  return res



def exec_func(func):
  try:
    return func(**json.loads(kwargs))
  except Exception as e:
    print(e)
    return None




# if __name__ == '__main__':
#   # print(fetch_photospectra(180.1082394033822, 0.2996335454281737))
#   print(plot_photospectra(180.1082394033822, 0.2996335454281737))
