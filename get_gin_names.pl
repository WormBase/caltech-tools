#!/usr/bin/perl

# generate mapping of wbgenes to their possible names, with same names to different genes in reverse priority in @tables.  2015 15 16
#
# tazendra moved from kerkhoff to chen, which broke the db connection by ip address.  Changed to the Chen IP address, even
# though tazendra probably not updating gene data anymore.  Tested that can connect to dockerized prod, but that needs a 
# user/pass that we shouldn't save in the script, so emailing with raymond about how we should proceed.  2024 10 21

use strict;
use warnings;
use DBI;

# my $dbh = DBI->connect ( "dbi:Pg:dbname=caltech_curation;host=caltech-curation.textpressolab.com", "<user>", "<pass>") or die "Cannot connect to database!\n";     # tazendra moved to caltech dockerized prod, which requires postgres user/pass that are not getting committed on the script
my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb;host=131.215.76.22", "", "") or die "Cannot connect to database!\n";     # tazendra moved to Chen
# my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb;host=131.215.52.76", "", "") or die "Cannot connect to database!\n";     # for remote access tazendra Kerckhoff
# my $dbh = DBI->connect ( "dbi:Pg:dbname=wobrdb", "", "") or die "Cannot connect to database!\n";
my $result;

  my %geneNameToId; my %geneIdToName;
#   my @tables = qw( gin_locus );
  my @tables = qw( gin_wbgene gin_seqname gin_synonyms gin_locus );
#   my @tables = qw( gin_seqname gin_synonyms gin_locus );
  foreach my $table (@tables) {
    my $result = $dbh->prepare( "SELECT * FROM $table;" );
    $result->execute();
    while (my @row = $result->fetchrow()) {
      my $id                 = "WBGene" . $row[0];
      my $name               = $row[1];
      my ($lcname)           = lc($name);
      $geneIdToName{$id}     = $name;
#       $geneNameToId{$lcname} = $id; 
      $geneNameToId{$name}   = $id; } }
#   return (\%geneNameToId, \%geneIdToName);

my $outfile = '/home/azurebrd/cron/gin_names/gin_names.txt';
open (OUT, ">$outfile") or die "Cannot create $outfile : $!";
foreach my $name (sort { $geneNameToId{$a} cmp $geneNameToId{$b} } keys %geneNameToId) {
  my $id = $geneNameToId{$name};
  my $primary = '';
  if ($geneIdToName{$id} eq $name) { $primary = 'primary'; }
  print OUT qq($id\t$name\t$primary\n);
} # foreach my $name (sort keys %geneNameToId)
close (OUT) or die "Cannot close $outfile : $!";
