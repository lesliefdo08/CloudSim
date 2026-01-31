"""
Educational tooltips for Storage concepts (S3 vs EBS)
"""

# S3 (Object Storage) Tooltips
STORAGE_TOOLTIPS = {
    's3_overview': {
        'title': '📦 Amazon S3 (Simple Storage Service)',
        'description': 'Object storage for any amount of data',
        'details': [
            '• <b>Use case:</b> Store files, backups, media, static websites',
            '• <b>Structure:</b> Buckets contain objects (files)',
            '• <b>Access:</b> Via HTTP/HTTPS URLs',
            '• <b>Durability:</b> 99.999999999% (11 nines)',
            '• <b>Pricing:</b> Pay per GB stored and transferred'
        ]
    },
    
    'bucket': {
        'title': '🪣 S3 Bucket',
        'description': 'Container for objects stored in S3',
        'details': [
            '• Must have globally unique name',
            '• Can store unlimited objects',
            '• Cannot be nested (no bucket-in-bucket)',
            '• Can have versioning, lifecycle policies',
            '• Can host static websites'
        ]
    },
    
    'object': {
        'title': '📄 S3 Object',
        'description': 'File stored in an S3 bucket',
        'details': [
            '• Max size: 5 TB per object',
            '• Has key (filename), value (content), metadata',
            '• Immutable (create new version to change)',
            '• Can have tags, ACLs, storage class'
        ]
    },
    
    'storage_class': {
        'title': '📊 S3 Storage Classes',
        'description': 'Different storage tiers for cost optimization',
        'details': [
            '• <b>Standard:</b> Frequent access, high availability',
            '• <b>Intelligent-Tiering:</b> Auto-moves between tiers',
            '• <b>Standard-IA:</b> Infrequent access, lower cost',
            '• <b>Glacier:</b> Archive, retrieval in minutes/hours',
            '• <b>Deep Archive:</b> Lowest cost, 12h retrieval'
        ]
    },
    
    'versioning': {
        'title': '🔄 S3 Versioning',
        'description': 'Keep multiple versions of objects',
        'details': [
            '• Protects from accidental deletion',
            '• Each version has unique ID',
            '• Can restore previous versions',
            '• Adds storage costs for old versions',
            '• Cannot be disabled, only suspended'
        ]
    }
}

# EBS (Block Storage) Tooltips
VOLUME_TOOLTIPS = {
    'ebs_overview': {
        'title': '💾 Amazon EBS (Elastic Block Store)',
        'description': 'Block-level storage for EC2 instances',
        'details': [
            '• <b>Use case:</b> Operating systems, databases, applications',
            '• <b>Structure:</b> Block devices attached to instances',
            '• <b>Access:</b> Direct file system access (mount point)',
            '• <b>Performance:</b> Low latency, high IOPS',
            '• <b>Limitation:</b> One volume = one instance (except io2)'
        ]
    },
    
    'volume': {
        'title': '💽 EBS Volume',
        'description': 'Virtual hard drive for EC2 instances',
        'details': [
            '• Like a physical hard drive or SSD',
            '• Must be in same AZ as instance',
            '• Persists independently from instance',
            '• Can be attached/detached while running',
            '• Can take snapshots for backup'
        ]
    },
    
    'volume_types': {
        'title': '⚡ EBS Volume Types',
        'description': 'Different performance characteristics',
        'details': [
            '• <b>gp3/gp2:</b> General Purpose SSD (balanced)',
            '• <b>io2/io1:</b> Provisioned IOPS SSD (databases)',
            '• <b>st1:</b> Throughput HDD (big data)',
            '• <b>sc1:</b> Cold HDD (infrequent access)',
            '• Choose based on IOPS and throughput needs'
        ]
    },
    
    'snapshot': {
        'title': '📸 EBS Snapshot',
        'description': 'Point-in-time backup of EBS volume',
        'details': [
            '• Stored in S3 (incremental backups)',
            '• Can create volume from snapshot',
            '• Can copy across regions',
            '• First snapshot is full, rest are incremental',
            '• Can create while volume is in use'
        ]
    },
    
    'encryption': {
        'title': '🔒 EBS Encryption',
        'description': 'Data encryption at rest and in transit',
        'details': [
            '• Uses AWS KMS keys',
            '• Encrypts data, snapshots, volumes from snapshots',
            '• No performance impact',
            '• Cannot change encryption after creation',
            '• Enabled by default in many regions'
        ]
    }
}

# Comparison Tooltips
COMPARISON_TOOLTIPS = {
    's3_vs_ebs': {
        'title': '🔄 S3 vs EBS: When to Use What?',
        'description': 'Choosing the right storage type',
        'details': [
            '<b>Use S3 when:</b>',
            '• Storing files, images, videos, backups',
            '• Sharing data across multiple instances',
            '• Building static websites',
            '• Archiving data long-term',
            '',
            '<b>Use EBS when:</b>',
            '• Running operating system',
            '• Hosting databases (MySQL, PostgreSQL)',
            '• Need low-latency block storage',
            '• Running applications that need file system'
        ]
    }
}

def get_storage_tooltip(key: str) -> dict:
    """Get storage tooltip by key"""
    return STORAGE_TOOLTIPS.get(key) or VOLUME_TOOLTIPS.get(key) or COMPARISON_TOOLTIPS.get(key)
