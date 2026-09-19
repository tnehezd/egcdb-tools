import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u

def main():
    csv_path = "./ngc1637_cepheids_official_catalog.csv"
    input_dir = "./hla_exposures"
    output_png = "./ngc1637_cepheids_clean_mosaic.png"

    if not os.path.exists(csv_path):
        print(f"❌ Catalog file '{csv_path}' not found! Run extract_exact_coords.py first.")
        return

    # 1. Load the reconstructed J2000 coordinate database
    df = pd.read_csv(csv_path)

    # SN 1999em certified anchor coordinate
    sn_ra = 70.366471
    sn_dec = -2.857964
    sn_coord = SkyCoord(ra=sn_ra, dec=sn_dec, unit=(u.deg, u.deg))

    # Define paths for the clean, cosmic-ray rejected Drizzle FITS files
    pc_fits = os.path.join(input_dir, "hst_09155_01_wfpc2_f555w_pc_drz.fits")
    wf_fits = os.path.join(input_dir, "hst_09155_01_wfpc2_f555w_wf_drz.fits")

    if not os.path.exists(pc_fits) or not os.path.exists(wf_fits):
        print("❌ Missing clean drz FITS files inside 'hla_exposures/' folder!")
        return

    # 2. Set up a professional side-by-side 1x2 panel layout
    fig, axs = plt.subplots(1, 2, figsize=(18, 9), dpi=150)
    
    # Configuration tuple for the loop: (panel_index, fits_path, target_chip_filter, panel_title)
    panels = [
        (0, pc_fits, ["PC1"], "Planetary Camera 1 (PC1) - High Resolution Core"),
        (1, wf_fits, ["WF2", "WF3", "WF4"], "Wide Field Mosaic (WF2, WF3, WF4) - Galaxy Arms")
    ]

    for idx, path, chip_filter, title in panels:
        ax = axs[idx]
        
        with fits.open(path) as hdul:
            # Extract the pristine science imaging extension layer (SCI)
            header = None
            img_data = None
            for hdu in hdul:
                if hdu.header.get('EXTNAME') == 'SCI     ' or hdu.header.get('NAXIS') == 2:
                    header = hdu.header
                    img_data = hdu.data
                    break
            if header is None:
                header = hdul.header
                img_data = hdul.data

            # Initialize the absolute WCS celestial mapping vector for the background frame
            wcs = WCS(header)
            
            # Contrast enhancement using percentile clipping to drop detector background floor noise
            vmin, vmax = np.percentile(img_data, [0.5, 98.5])
            ax.imshow(img_data, cmap='gray', origin='lower', vmin=vmin, vmax=vmax)
            ax.set_title(title, fontsize=14, weight='bold', pad=10)
            ax.grid(False)

            # --- PLOT SUPERNOVA SN 1999em (Only on the Wide Field mosaic panel) ---
            if idx == 1:
                sn_pixel = wcs.world_to_pixel_values(np.array([[sn_ra, sn_dec]]))
                # 🛠️ FIXED Matrix Indexing
                sn_px = float(sn_pixel[0][0])
                sn_py = float(sn_pixel[0][1])
                
                if 0 <= sn_px <= img_data.shape[1] and 0 <= sn_py <= img_data.shape[0]:
                    ax.scatter(sn_px, sn_py, color='red', marker='*', s=400, edgecolors='black', linewidths=1.5, zorder=5, label="SN 1999em")
                    ax.text(sn_px + 20, sn_py + 20, "SN 1999em", color='red', fontsize=11, weight='bold',
                            bbox=dict(facecolor='black', alpha=0.6, boxstyle='round,pad=0.2', edgecolor='none'), zorder=6)

            # --- PLOT FILTERED CEPHEIDS VIA J2000 CELESTIAL POSITIONS ---
            group = df[df["chip"].isin(chip_filter)]
            
            for _, row in group.iterrows():
                world_coord = np.array([[row["ra_deg"], row["dec_deg"]]])
                pixel_coords = wcs.world_to_pixel_values(world_coord)
                # 🛠️ FIXED Matrix Indexing
                px = float(pixel_coords[0][0])
                py = float(pixel_coords[0][1])
                
                # Render targets strictly contained within the active image boundary framework
                if 0 <= px <= img_data.shape[1] and 0 <= py <= img_data.shape[0]:
                    ax.scatter(px, py, s=180, facecolors='none', edgecolors='#00ff00', linewidths=1.8, zorder=4)
                    ax.text(px + 15, py + 15, str(int(row["hstphot_id"])), color='#00ff00', fontsize=9, weight='bold',
                            bbox=dict(facecolor='black', alpha=0.6, boxstyle='round,pad=0.1', edgecolor='none'), zorder=5)
            
            ax.set_xlim(0, img_data.shape[1])
            ax.set_ylim(0, img_data.shape[0])
            ax.set_xlabel("Image X pixel", fontsize=11)
            ax.set_ylabel("Image Y pixel", fontsize=11)

    # Apply formatting structure to prevent visual overlaps
    plt.suptitle("NGC 1637 Reconstructed Cepheids & SN 1999em on Clean HLA Drizzled Frames", fontsize=18, weight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.savefig(output_png, bbox_inches='tight')
    plt.close()

    print("-" * 85)
    print("CLEAN SIDE-BY-SIDE OVERLAY MOSAIC IMAGE SUCCESSFULLY GENERATED!")
    print(f"The pristine finding chart has been saved here:\n {os.path.abspath(output_png)}")
    print("-" * 85)

if __name__ == "__main__":
    main()
