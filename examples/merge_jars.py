import os
import zipfile
import tempfile

def find_jars(base_dir):
    """Recursively find all JAR files in the given directory."""
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".jar"):
                yield os.path.join(root, file)

def extract_jar(jar_path, dest_dir):
    """Extract a JAR file to the given directory."""
    with zipfile.ZipFile(jar_path, 'r') as jar:
        jar.extractall(dest_dir)

def create_uber_jar(dest_jar, source_dir):
    """Create an uber JAR from the contents of the given directory."""
    with zipfile.ZipFile(dest_jar, 'w') as uber_jar:
        for foldername, subfolders, filenames in os.walk(source_dir):
            for filename in filenames:
                filepath = os.path.join(foldername, filename)
                arcname = os.path.relpath(filepath, source_dir)
                uber_jar.write(filepath, arcname)

def main(indir, outdir):
    temp_dir = tempfile.mkdtemp()

    # Find and extract all JARs to the temp directory
    for jar in find_jars(indir):
        extract_jar(jar, temp_dir)

    # Create the uber JAR
    create_uber_jar(os.path.join(outdir, "uber.jar"), temp_dir)

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser("Merge jars")
    parser.add_argument("indir", help="Directory to crawl thru")
    parser.add_argument("outdir", help="Directory to save uber jar to")
    args = parser.parse_args()
    main(args.indir, args.outdir)
