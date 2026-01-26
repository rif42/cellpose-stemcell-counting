"""
Batch Confluency Calculator

Applies Cellpose confluency calculation to all images in a directory
and generates a summary report with CSV output.
"""

import os
import sys
import csv
from datetime import datetime

# Import the confluency calculator from local module
from confluency_cellpose import calculate_confluency


def batch_process_confluency(
    input_dir: str,
    output_dir: str = None,
    model_name: str = 'cpsam',
    diameter: float = 50,
    flow_threshold: float = 2.0,
    cellprob_threshold: float = -1,
    niter: int = 2000,
    use_gpu: bool = True,
    clahe_clip_limit: float = 2.0
):
    """
    Process all images in a directory and calculate confluency.
    
    Args:
        input_dir: Directory containing input images
        output_dir: Directory for output files (defaults to input_dir)
        model_name: Cellpose model to use
        diameter: Expected cell diameter
        flow_threshold: Flow error threshold
        cellprob_threshold: Cell probability threshold (logit)
        niter: Number of flow iterations
        use_gpu: Whether to use GPU
        clahe_clip_limit: CLAHE clip limit for preprocessing
    
    Returns:
        List of result dictionaries
    """
    
    if output_dir is None:
        output_dir = input_dir
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Find all image files
    valid_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp'}
    image_files = []
    
    for f in os.listdir(input_dir):
        ext = os.path.splitext(f)[1].lower()
        if ext in valid_extensions:
            image_files.append(f)
    
    image_files.sort()
    
    print(f"\n{'='*70}")
    print(f"BATCH CONFLUENCY PROCESSING")
    print(f"{'='*70}")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Images found: {len(image_files)}")
    print(f"Model: {model_name}")
    print(f"Diameter: {diameter}")
    print(f"Cell probability threshold: {cellprob_threshold}")
    print(f"CLAHE clip limit: {clahe_clip_limit}")
    print(f"{'='*70}\n")
    
    # Process each image
    results = []
    
    for i, filename in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] Processing: {filename}")
        print("-" * 50)
        
        image_path = os.path.join(input_dir, filename)
        
        try:
            result = calculate_confluency(
                image_path=image_path,
                model_name=model_name,
                diameter=diameter,
                flow_threshold=flow_threshold,
                cellprob_threshold=cellprob_threshold,
                niter=niter,
                use_gpu=use_gpu,
                save_outputs=True,
                output_dir=output_dir,
                clahe_clip_limit=clahe_clip_limit
            )
            
            results.append({
                'filename': filename,
                'confluency': result['confluency'],
                'cell_pixels': result['cell_area_pixels'],
                'total_pixels': result['total_area_pixels'],
                'status': 'success'
            })
            
        except Exception as e:
            print(f"ERROR processing {filename}: {str(e)}")
            results.append({
                'filename': filename,
                'confluency': None,
                'cell_pixels': None,
                'total_pixels': None,
                'status': f'error: {str(e)}'
            })
    
    # Generate summary report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f"confluency_report_{timestamp}.csv")
    
    with open(report_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['filename', 'confluency', 'cell_pixels', 'total_pixels', 'status'])
        writer.writeheader()
        writer.writerows(results)
    
    # Print summary
    successful = [r for r in results if r['status'] == 'success']
    
    print(f"\n{'='*70}")
    print(f"BATCH PROCESSING COMPLETE")
    print(f"{'='*70}")
    print(f"Processed: {len(results)} images")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(results) - len(successful)}")
    
    if successful:
        confluencies = [r['confluency'] for r in successful]
        print(f"\nConfluency Statistics:")
        print(f"  Min: {min(confluencies):.2f}%")
        print(f"  Max: {max(confluencies):.2f}%")
        print(f"  Mean: {sum(confluencies)/len(confluencies):.2f}%")
    
    print(f"\nReport saved: {report_path}")
    print(f"{'='*70}\n")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Batch process images for confluency calculation'
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
        '--cellprob_threshold', '-cp',
        type=float,
        default=-1,
        help='Cell probability threshold in logits (default: -1)'
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
        sys.exit(1)
    
    batch_process_confluency(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        model_name=args.model,
        diameter=args.diameter,
        flow_threshold=args.flow_threshold,
        cellprob_threshold=args.cellprob_threshold,
        use_gpu=not args.cpu,
        clahe_clip_limit=args.clahe_clip
    )
