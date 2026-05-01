import base64
import json
from io import BytesIO

import matplotlib
import matplotlib.patheffects as PathEffects
import matplotlib.ticker as tck
import numpy as np
import requests
from matplotlib import pyplot as plt

matplotlib.use('Agg')
kwargs = None



EMISSION_LINES = [
  {'wl': 1033.82, 'text': r'O$_\textsc{VI}$', },
  {'wl': 1215.24, 'text': r'Ly$\alpha$', },
  {'wl': 1240.81, 'text': 'N$_\text{V}$', },
  {'wl': 1305.53, 'text': 'O$_\text{I}$', },
  {'wl': 1335.31, 'text': 'C$_\text{II}$', },
  {'wl': 1397.61, 'text': 'Si$_\text{IV}$', },
  {'wl': 1399.8, 'text': 'Si$_\text{IV}$ + O$_\text{IV}$', },
  {'wl': 1549.48, 'text': 'C$_\text{IV}$', },
  {'wl': 1640.4, 'text': 'He$_\text{II}$', },
  {'wl': 1665.85, 'text': r'O$_\text{III}$', },
  {'wl': 1857.4, 'text': r'Al$_\text{III}$', },
  {'wl': 1908.734, 'text': r'C$_\text{III}$', },
  {'wl': 2326.0, 'text': r'C$_\text{II}$', },
  {'wl': 2439.5, 'text': r'Ne$_\text{IV}$', },
  {'wl': 2799.117, 'text': r'Mg$_\text{II}$', },
  {'wl': 3346.79, 'text': r'Ne$_\text{V}$', 'ha': 'right'},
  {'wl': 3426.85, 'text': r'Ne$_\text{VI}$', 'ha': 'left'},
  # {'wl': 3727.092, 'text': r'O$_\text{II}$', 'ha': 'right'},
  {'wl': 3729.875, 'text': r'O$_\text{II}$', 'ha': 'left'},
  {'wl': 3889.0, 'text': r'He$_\text{I}$', },
  {'wl': 4072.3, 'text': r'S$_\text{II}$', 'ha': 'right'},
  {'wl': 4102.89, 'text': r'H$\delta$', 'ha': 'left'},
  {'wl': 4341.68, 'text': r'H$\gamma$', },
  {'wl': 4364.436, 'text': r'O$_\text{III}$', 'ha': 'left'},
  {'wl': 4862.68, 'text': r'H$\beta$', 'ha': 'right'},
  # {'wl': 4932.603, 'text': r'O$_\text{III}$', },
  # {'wl': 4960.295, 'text': r'O$_\text{III}$', },
  {'wl': 5008.240, 'text': r'O$_\text{III}$', 'ha': 'left'},
  {'wl': 6302.046, 'text': r'O$_\text{I}$', 'ha': 'right'},
  {'wl': 6365.536, 'text': r'O$_\text{I}$', },
  # {'wl': 6529.03, 'text': r'N$_\text{I}$', },
  {'wl': 6549.86, 'text': r'N$_\text{II}$', 'ha': 'right'},
  {'wl': 6564.61, 'text': r'H$\alpha$', },
  {'wl': 6585.27, 'text': r'N$_\text{II}$', 'ha': 'left'},
  # {'wl': 6718.29, 'text': r'S$_\text{II}$',},
  {'wl': 6732.67, 'text': r'S$_\text{II}$', 'ha': 'left'},
]

ABSORPTION_LINES = [
  {'wl': 3934.777, 'text': 'K', 'ha': 'right' },
  {'wl': 3969.588, 'text': 'H', 'ha': 'left' },
  {'wl': 4305.61 , 'text': 'G', },
  {'wl': 5176.7, 'text': 'Mg', },
  {'wl': 5895.6, 'text': 'Na', },
  {'wl': 8500.36, 'text': r'Ca$_\text{II}$', 'ha': 'right'},
  {'wl': 8544.44, 'text': r'Ca$_\text{II}$', 'ha': 'center'},
  {'wl': 8664.52, 'text': r'Ca$_\text{II}$', 'ha': 'left'},
]



def bytes_to_base64(buffer, fmt: str = 'jpeg'):
  buffer.seek(0)
  img_b64 = base64.b64encode(buffer.getvalue()).decode('utf8')
  return f'data:image/{fmt};base64,{img_b64}'



def find_nearest_index(array, value):
  return (np.abs(array - value)).argmin()



def fetch_sparcl_spectrum(sparcl_id, **kwargs):
  proxy = 'https://astrotools.vercel.app/proxy/'
  url = 'https:/astrosparcl.datalab.noirlab.edu/sparc/spectras/?include=wavelength,flux,redshift&format=json'
  res = requests.post(f'{proxy}{url}', json=[sparcl_id], timeout=10)
  data = res.json()[1]
  flux = data['flux']
  wl = data['wavelength']
  z = data['redshift']
  return wl, flux, z



def include_line_annotations(x, y, wl, z, text, color, emission, ax: plt.Axes, ha='center'):
  wl = wl * (1+z)
  
  if wl > x[-1] or wl < x[0]:
    return
  
  direction = 1 if emission else -1
  
  lim = ax.get_ylim()
  delta = (abs(lim[0]) + abs(lim[1])) * 0.08
  
  i = find_nearest_index(x, wl)
  em_flux = y[i]
  
  y01 = [em_flux + direction*delta*1.5, em_flux + direction*delta]
  va = 'bottom' if emission else 'top'
  text_pos = em_flux + direction*delta*1.55
  
  ax.vlines(wl, min(y01), max(y01), lw=0.8, color=color)
  txt = ax.text(wl, text_pos, text, fontsize=8, va=va, ha=ha)
  txt.set_path_effects([PathEffects.withStroke(linewidth=1.5, foreground='w')])



def include_all(x, y, z, ax: plt.Axes):
  for line in ABSORPTION_LINES:
    include_line_annotations(x=x, y=y, z=z, color='red', emission=False, ax=ax, **line)
  for line in EMISSION_LINES:
    include_line_annotations(x=x, y=y, z=z, color='blue', emission=True, ax=ax, **line)
  


def plot_desi_spectrum(
  sparcl_id: str,
  ra: float = None,
  dec: float = None,
  z: float = None,
  z_err: float = None,
  spec_class: str = None,
  dataset: str = 'DESI',
  boxcar_width: int = 6,
  lower_percentile: float = 0.1,
  upper_percentile: float = 99.9,
  **kwargs
):
  wl, flux, z_aux = fetch_sparcl_spectrum(sparcl_id)
  if z is None:
    z = z_aux
  wl = np.asarray(wl)
  flux = np.asarray(flux)
  
  f = plt.figure(figsize=(7,5))
  ax = f.subplots()
  
  try:
    boxcar_width = int(boxcar_width)
    flux_smooth = np.convolve(flux, np.ones(boxcar_width)/boxcar_width, mode='same')
  except Exception:
    flux_smooth = flux
  
  ax.plot(wl, flux, color='k', lw=0.2, alpha=0.5)
  ax.plot(wl, flux_smooth, color='k', lw=0.5)
  
  y_min, y_max = np.percentile(flux, [lower_percentile, upper_percentile])
  y_max = max(y_max, flux_smooth.max()*1.1)
  y_min = min(y_min, flux_smooth.min()*1.1)
  ax.set_ylim(y_min, y_max)
  ax.set_xlim(wl[0] - 100, wl[-1] + 100)
  
  include_all(wl, flux_smooth, z, ax)
  
  title = f'Survey: {dataset}'
  if ra is not None and dec is not None:
    title += f'\nRA: {ra:.4f}  Dec: {dec:.4f}'
  if z is not None and z_err is not None:
    title += '\n' + fr'Redshift: ${z:.5f} \pm {z_err:.5f}$  '
  elif z is not None:
    title += '\n' + f'Redshift: ${z:.5f}$  '
  if spec_class is not None:
    title += f'Class: {spec_class}'
    
  ax.set_title(title, loc='left')
  
  ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
  ax.xaxis.set_minor_locator(tck.AutoMinorLocator())
  ax.set_xlabel('Wavelength (Angstrons)')
  ax.set_ylabel(r'$f_{\lambda} (10^{-17} \text{erg}/\text{s}/\text{cm}^{2}/\text{Angstrons})$')
  ax.tick_params(axis='both', which='both', direction='in', right=True, top=True)
  ax.tick_params(axis='both', which='major', length=7)
  ax.tick_params(axis='both', which='minor', length=3.5)
  
  # f.savefig('/home/natan/Downloads/x.png', dpi=300, pad_inches=0.1, bbox_inches='tight')
  
  buffer = BytesIO()
  f.savefig(buffer, format='png', dpi=150, pad_inches=0.1, bbox_inches='tight')
  plt.close(f)
  return bytes_to_base64(buffer, fmt='png')



def test_plot(ra, dec):
  f = plt.figure(figsize=(3,3))
  ax = f.subplots()
  ax.text(0.02, 0.5, str(ra) + ' ' + str(dec))
  buffer = BytesIO()
  f.savefig(buffer, format='jpg', pad_inches=0.01, bbox_inches='tight')
  plt.close(f)
  return bytes_to_base64(buffer)



def exec_func(func):
  try:
    y = func(**json.loads(kwargs))
    return y
  except Exception as e:
    print(e)
    return None


# if __name__ == '__main__':
#   print(plot_desi_spectrum('5bccbbd5-87f0-11ef-93c8-525400f334e1'))