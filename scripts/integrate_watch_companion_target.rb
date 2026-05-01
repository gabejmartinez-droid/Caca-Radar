#!/usr/bin/env ruby
# frozen_string_literal: true

require 'fileutils'
require 'xcodeproj'

PROJECT_DIR = File.expand_path('../frontend/ios/WatchCompanion', __dir__)
PROJECT_PATH = File.join(PROJECT_DIR, 'WatchCompanion.xcodeproj')
INFO_PLIST_PATH = '../WatchCompanionApp/Info.plist'
TARGET_NAME = 'CacaRadarWatch'
WATCH_BUNDLE_ID = 'com.jefe.cacaradar.watchkitapp'
WATCH_DEPLOYMENT_TARGET = '10.0'

FileUtils.mkdir_p(PROJECT_DIR)

project =
  if File.exist?(PROJECT_PATH)
    Xcodeproj::Project.open(PROJECT_PATH)
  else
    Xcodeproj::Project.new(PROJECT_PATH)
  end

project.root_object.attributes['LastUpgradeCheck'] = '1600'
project.root_object.attributes['LastSwiftUpdateCheck'] = '1600'

watch_target = project.targets.find { |target| target.name == TARGET_NAME }
unless watch_target
  watch_target = project.new_target(:watch2_app, TARGET_NAME, :watchos, WATCH_DEPLOYMENT_TARGET, project.products_group, :swift, TARGET_NAME)
end

main_group = project.main_group
support_group = main_group.children.find { |child| child.isa == 'PBXGroup' && child.display_name == 'Support' } || main_group.new_group('Support', '../WatchCompanionApp')

source_refs = %w[
  CacaRadarWatchApp.swift
  ContentView.swift
  PhoneSessionBridge.swift
].map do |filename|
  main_group.files.find { |child| child.path == filename } || main_group.new_file(filename)
end

main_group.set_source_tree('<group>')
support_group.set_source_tree('<group>')
info_plist_ref = support_group.files.find { |child| child.path == 'Info.plist' } || support_group.new_file('Info.plist')

watch_target.add_file_references(source_refs)

watch_target.build_configurations.each do |config|
  build_settings = config.build_settings
  build_settings['CODE_SIGN_STYLE'] = 'Automatic'
  build_settings['CURRENT_PROJECT_VERSION'] = '24'
  build_settings['DEVELOPMENT_TEAM'] = 'Z3SH6Z4GL6'
  build_settings['GENERATE_INFOPLIST_FILE'] = 'NO'
  build_settings['INFOPLIST_FILE'] = INFO_PLIST_PATH
  build_settings['MARKETING_VERSION'] = '1.1.22'
  build_settings['PRODUCT_BUNDLE_IDENTIFIER'] = WATCH_BUNDLE_ID
  build_settings['PRODUCT_NAME'] = TARGET_NAME
  build_settings['SDKROOT'] = 'watchos'
  build_settings['SKIP_INSTALL'] = 'NO'
  build_settings['SUPPORTED_PLATFORMS'] = 'watchos watchsimulator'
  build_settings['SWIFT_VERSION'] = '5.0'
  build_settings['TARGETED_DEVICE_FAMILY'] = '4'
  build_settings['WATCHOS_DEPLOYMENT_TARGET'] = WATCH_DEPLOYMENT_TARGET
end

target_attributes = project.root_object.attributes['TargetAttributes'] ||= {}
target_attributes[watch_target.uuid] ||= {}
target_attributes[watch_target.uuid]['CreatedOnToolsVersion'] ||= '16.0'
target_attributes[watch_target.uuid]['DevelopmentTeam'] = 'Z3SH6Z4GL6'
target_attributes[watch_target.uuid]['ProvisioningStyle'] = 'Automatic'

project.save
