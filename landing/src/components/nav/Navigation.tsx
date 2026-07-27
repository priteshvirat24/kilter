'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Activity, ShieldCheck, Cpu, Terminal, Layers } from 'lucide-react';

export const Navigation: React.FC = () => {
  const pathname = usePathname();

  const navLinks = [
    { name: 'Overview', href: '/', icon: Activity },
    { name: '4-Layer Diff', href: '/engine', icon: Layers },
    { name: 'Safety Gate', href: '/safety', icon: ShieldCheck },
    { name: 'Live Suite', href: '/demo', icon: Terminal },
    { name: 'Specifications', href: '/specs', icon: Cpu },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass-nav px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-8 h-8 rounded bg-[#1A1B1E] flex items-center justify-center font-bold text-[#FDFBF7] tracking-tighter shadow-md group-hover:bg-[#C84B31] transition-colors">
            K
          </div>
          <div className="flex flex-col">
            <span className="font-extrabold tracking-wider text-sm text-[#1A1B1E]">KILTER</span>
            <span className="text-[10px] uppercase text-[#6A707A] font-mono tracking-tighter">Active MCP Metrology</span>
          </div>
        </Link>

        <nav className="hidden md:flex items-center space-x-1 bg-[#EBE5DC]/50 p-1 rounded-full border border-black/5">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.name}
                href={link.href}
                className={`flex items-center space-x-2 px-4 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-all ${
                  isActive
                    ? 'bg-[#1A1B1E] text-[#FDFBF7] shadow-sm'
                    : 'text-[#2C2E33] hover:text-[#C84B31] hover:bg-[#FAF8F5]/80'
                }`}
              >
                <Icon size={14} className={isActive ? 'text-[#E08E45]' : 'text-[#6A707A]'} />
                <span>{link.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center space-x-4">
          <div className="hidden lg:flex items-center space-x-2 px-3 py-1 bg-[#3B5249]/10 rounded-full border border-[#3B5249]/20">
            <span className="w-2 h-2 rounded-full bg-[#3B5249] animate-pulse"></span>
            <span className="text-[11px] font-mono text-[#3B5249] font-medium uppercase tracking-tight">
              Engine Ready
            </span>
          </div>
          <Link
            href="/demo"
            className="px-4 py-2 bg-[#1A1B1E] hover:bg-[#C84B31] text-[#FDFBF7] text-xs font-semibold uppercase tracking-wider rounded transition-colors shadow-sm flex items-center space-x-1.5"
          >
            <span>Launch Suite</span>
            <span className="font-mono text-[10px] text-[#E08E45] opacity-80">:3005</span>
          </Link>
        </div>
      </div>
    </header>
  );
};
