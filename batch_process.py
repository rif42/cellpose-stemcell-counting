"""
Batch Cell Segmentation using Cellpose

Processes all images in a directory and generates segmentation masks.
Applies CLAHE preprocessing before running Cellpose.
"""

import os
import glob
import time
import numpy as np
import cv2
from cellpose import models, io


def apply_clahe_to_image(img, clip_limit=2.0, tile_grid_size=(8, 8)):
    """Apply CLAHE preprocessing to an image."""
    if img.ndim == 3:
        img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        img_gray = img
    
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    return clahe.apply(img_gray)


def batch_process(
    input_dir: str,
    output_dir: str = None,
    model_name: str = 'cpsam',
    diameter: float = 50,
    flow_threshold: float = 2.0,
    cellprob_threshold: float = -0.5,
    niter: int = 2000,
    use_gpu: bool = True,
    apply_clahe: bool = True,
    clahe_clip_limit: float = 2.0
):
    """
    Batch process images for cell segmentation.
    
    Args:
        input_dir: Directory containing input images
        output_dir: Directory for output files (defaults to input_dir)
        model_name: Cellpose model to use
        diameter: Expected cell diameter
        flow_threshold: Flow error threshold
        cellprob_threshold: Cell probability threshold
        niter: Number of flow iterations
        use_gpu: Whether to use GPU
        apply_clahe: Whether to apply CLAHE preprocessing
        clahe_clip_limit: CLAHE clip limit
    """
    
    if output_dir is None:
        output_dir = input_dir
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    print(f"Loading model: {model_name}")
    model = models.CellposeModel(gpu=use_gpu, pretrained_model=model_name)

    # Get list of images
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.tif', '*.tiff', '*.bmp']
    image_files = []
    for ext in extensions:
        image_files.extend(glob.glob(os.path.join(input_dir, ext)))
    
    image_files.sort()

    print(f"Found {len(image_files)} images in {input_dir}")

    # Track results
    processing_results = []
    start_time = time.time()

    for img_path in image_files:
        img_name = os.path.basename(img_path)
        print(f"Processing {img_name}...")
        
        try:
            # Read image
            img = io.imread(img_path)
            
            # Apply CLAHE if enabled
            if apply_clahe:
                img = apply_clahe_to_image(img, clahe_clip_limit)
            
            # Run evaluation
            masks, flows, styles = model.eval(
                img, 
                diameter=diameter,
                flow_threshold=flow_threshold,
                cellprob_threshold=cellprob_threshold,
                niter=niter
            )

            # Save results as *_seg.npy
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            output_path = os.path.join(output_dir, base_name)
            
            io.masks_flows_to_seg(img, masks, flows, output_path)
            
            # Count ROIs
            num_rois = len(np.unique(masks)) - 1
            print(f"Saved result to {output_path}_seg.npy - Detected {num_rois} ROIs")
            
            processing_results.append({
                'filename': img_name,
                'roi_count': num_rois,
                'status': 'Success'
            })

        except Exception as e:
            print(f"Error processing {img_name}: {e}")
            processing_results.append({
                'filename': img_name,
                'roi_count': 0,
                'status': f'Error: {str(e)}'
            })

    # Generate summary report
    end_time = time.time()
    total_time = end_time - start_time
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f"processing_report_{timestamp}.txt")
    
    with open(report_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("CELLPOSE BATCH PROCESSING REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("PROCESSING PARAMETERS:\n")
        f.write("-" * 80 + "\n")
        f.write(f"Model: {model_name}\n")
        f.write(f"Cell Diameter: {diameter}\n")
        f.write(f"Flow Threshold: {flow_threshold}\n")
        f.write(f"Cell Probability Threshold: {cellprob_threshold}\n")
        f.write(f"CLAHE Enabled: {apply_clahe}\n")
        f.write(f"Input Directory: {input_dir}\n")
        f.write(f"Output Directory: {output_dir}\n")
        f.write(f"Processing Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Processing Time: {total_time:.2f} seconds\n\n")
        
        f.write("PROCESSING RESULTS:\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Filename':<30} {'ROI Count':<15} {'Status':<35}\n")
        f.write("-" * 80 + "\n")
        
        total_rois = 0
        successful_count = 0
        
        for result in processing_results:
            f.write(f"{result['filename']:<30} {result['roi_count']:<15} {result['status']:<35}\n")
            if result['status'] == 'Success':
                total_rois += result['roi_count']
                successful_count += 1
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("SUMMARY STATISTICS:\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total Images Processed: {len(processing_results)}\n")
        f.write(f"Successfully Processed: {successful_count}\n")
        f.write(f"Failed: {len(processing_results) - successful_count}\n")
        f.write(f"Total ROIs Detected: {total_rois}\n")
        if successful_count > 0:
            f.write(f"Average ROIs per Image: {total_rois / successful_count:.2f}\n")
        f.write("=" * 80 + "\n")
    
    print(f"\n{'='*80}")
    print(f"Processing complete! Report saved to: {report_path}")
    print(f"Total images processed: {len(processing_results)}")
    print(f"Total ROIs detected: {total_rois}")
    print(f"{'='*80}")
    
    return processing_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Batch process images for cell segmentation using Cellpose'
    )
    parser.add_argument(
        'input_dir',
        type=str,
        help='Directory containing input images'
    )
    parser.add_argument(
        '--output_dir', '-o',
        type=str,
        default=None,
        help='Output directory (default: same as input)'
    )
    parser.add_argument(
        '--model', '-m',
        type=str,
        default='cpsam',
        help='Cellpose model name (default: cpsam)'
    )
    parser.add_argument(
        '--diameter', '-d',
        type=float,
        default=50,
        help='Expected cell diameter (default: 50)'
    )
    parser.add_argument(
        '--flow_threshold', '-ft',
        type=float,
        default=2.0,
        help='Flow error threshold (default: 2.0)'
    )
    parser.add_argument(
        '--cellprob_threshold', '-ct',
        type=float,
        default=-0.5,
        help='Cell probability threshold (default: -0.5)'
    )
    parser.add_argument(
        '--no-clahe',
        action='store_true',
        help='Disable CLAHE preprocessing'
    )
    parser.add_argument(
        '--clahe_clip',
        type=float,
        default=2.0,
        help='CLAHE clip limit (default: 2.0)'
    )
    parser.add_argument(
        '--cpu',
        action='store_true',
        help='Use CPU instead of GPU'
    )
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory not found: {args.input_dir}")
        exit(1)
    
    batch_process(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        model_name=args.model,
        diameter=args.diameter,
        flow_threshold=args.flow_threshold,
        cellprob_threshold=args.cellprob_threshold,
        use_gpu=not args.cpu,
        apply_clahe=not args.no_clahe,
        clahe_clip_limit=args.clahe_clip
    )
