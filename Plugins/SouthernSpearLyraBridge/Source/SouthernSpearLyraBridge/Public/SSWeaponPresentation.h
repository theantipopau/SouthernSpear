// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

class APawn;
class UStaticMeshComponent;

/** Shared lookups for weapon presentation (casings, muzzle light). */
struct SSBRIDGE_API FSSWeaponPresentation
{
	/**
	 * The shooter's held weapon mesh as the local viewer sees it, carrying one of Sockets: the first-person
	 * view model (only-owner-see) for the locally controlled player, the third-person weapon (Lyra's spawned
	 * weapon actor's static mesh) for everyone else, either one when the preferred view has none. Null when
	 * no visible mesh carries any of the sockets.
	 */
	static UStaticMeshComponent* FindViewerWeapon(APawn* Shooter, TConstArrayView<FName> Sockets);

	/** The first of Names that Mesh carries, or NAME_None. */
	static FName FirstSocket(const UStaticMeshComponent* Mesh, TConstArrayView<FName> Names);

	/** Imported socket names first (the FBX importer drops SOCKET_), then the Blender names. */
	static TConstArrayView<FName> MuzzleSockets();
	static TConstArrayView<FName> EjectSockets();
	static TConstArrayView<FName> EjectEndSockets();
};
