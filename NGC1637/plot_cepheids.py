import os
import json
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

def main():
    json_path = "./cepheids_cache.json"
    fits_filename = "u6fv0101m_c0m.fits"
    fits_path = os.path.join("./hla_exposures", fits_filename)
    output_png = "./ngc1637_cepheids_raw_4chips.png"

    if not os.path.exists(json_path) or not os.path.exists(fits_path):
        print(f"❌ Missing JSON file or the downloaded '{fits_filename}' file!")
        return

    # 1. Load dataset and raw FITS exposure
    with open(json_path, 'r', encoding='utf-8') as f:
        cepheids = json.load(f)
        
    with fits.open(fits_path) as hdul:
        print(f"📷 Successfully loaded raw Hubble frame: {fits_filename}")
        
        # Construct a 2x2 grid layout mirroring the layout structure from the paper
        fig, axs = plt.subplots(2, 2, figsize=(14, 14), dpi=150)
        
        # Grid assignment mapping for each detector chip block:
        plot_positions = {
            1: (0, 0, "Chip 1 (PC1)"),
            2: (0, 1, "Chip 2 (WF2)"),
            3: (1, 0, "Chip 3 (WF3)"),
            4: (1, 1, "Chip 4 (WF4)")
        }

        # Initialize background intensity mapping for all 4 CCDs
        for chip_idx in range(1, 5):
            row, col, title = plot_positions[chip_idx]
            ax = axs[row, col]
            
            # Extract raw 800x800 science pixel array data
            img_data = hdul[chip_idx].data
            
            # Apply dynamic percentile stretching for clear features visibility
            vmin, vmax = np.percentile(img_data, [1.0, 98.5])
            ax.imshow(img_data, cmap='gray', origin='lower', vmin=vmin, vmax=vmax)
            ax.set_title(title, fontsize=14, weight='bold')
            ax.grid(False)
            
            # Overlay the supernova landmark marker explicitly on the Wide Field 4 array
            if chip_idx == 4:
                ax.scatter(213.1, 407.8, color='red', marker='*', s=350, edgecolors='black', label="SN 1999em", zorder=5)
                ax.text(213.1 + 15, 407.8 + 15, "SN 1999em", color='red', fontsize=10, weight='bold',
                        bbox=dict(facecolor='black', alpha=0.6, boxstyle='round,pad=0.2', edgecolor='none'), zorder=6)

        # 2. Render Cepheid targets based purely on pristine native coordinate values (bypassing any WCS rotation steps)
        for star in cepheids:
            # 🛠️ Safe skip block to pass over the embedded metadata header description
            if star["id"] == "METADATA":
                continue

            chip_num = star["chip"]
            cx = star["x"]
            cy = star["y"]
            star_id = star["id"]
            
            if chip_num in plot_positions:
                row, col, _ = plot_positions[chip_num]
                ax = axs[row, col]
                
                # Draw marker circles anchored directly to hstphot ground-truth centroids
                ax.scatter(cx, cy, s=200, facecolors='none', edgecolors='#00ff00', linewidths=2.0, zorder=4)
                ax.text(cx + 15, cy + 15, str(star_id), color='#00ff00', fontsize=9, weight='bold',
                        bbox=dict(facecolor='black', alpha=0.6, boxstyle='round,pad=0.1', edgecolor='none'), zorder=5)

        # Fix the title overlap by adjusting the tight_layout bounding box layout
        plt.suptitle("NGC 1637 Cepheids and SN 1999em on Raw Native HST/WFPC2 Chips", fontsize=18, weight='bold', y=0.98)
        
        # rect=[left, bottom, right, top] -> leaves a 5% safety margin at the top for the main title
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        plt.savefig(output_png, bbox_inches='tight')
        plt.close()

        print("-" * 85)
        print("🎨 NATIVE 4-CHIP VISUAL OVERLAY IMAGE SUCCESSFULLY CREATION COMPLETE!")
        print(f"Publication-ready finding chart saved to:\n👉 {os.path.abspath(output_png)}")
        print("-" * 85)


if __name__ == "__main__":
    main()
