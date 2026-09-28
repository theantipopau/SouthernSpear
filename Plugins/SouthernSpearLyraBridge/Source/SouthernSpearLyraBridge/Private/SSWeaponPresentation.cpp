// Copyright Southern Spear. All Rights Reserved.

#include "SSWeaponPresentation.h"

#include "Components/StaticMeshComponent.h"
#include "GameFramework/Pawn.h"

TConstArrayView<FName> FSSWeaponPresentation::MuzzleSockets()
{
	static const FName Names[] = { TEXT("Muzzle"), TEXT("SOCKET_Muzzle") };
	return Names;
}

TConstArrayView<FName> FSSWeaponPresentation::EjectSockets()
{
	static const FName Names[] = { TEXT("Eject"), TEXT("SOCKET_Eject") };
	return Names;
}

TConstArrayView<FName> FSSWeaponPresentation::EjectEndSockets()
{
	static const FName Names[] = { TEXT("EjectEnd"), TEXT("SOCKET_EjectEnd") };
	return Names;
}

FName FSSWeaponPresentation::FirstSocket(const UStaticMeshComponent* Mesh, TConstArrayView<FName> Names)
{
	if (Mesh)
	{
		for (const FName& Name : Names)
		{
			if (Mesh->DoesSocketExist(Name))
			{
				return Name;
			}
		}
	}
	return NAME_None;
}

UStaticMeshComponent* FSSWeaponPresentation::FindViewerWeapon(APawn* Shooter, TConstArrayView<FName> Sockets)
{
	if (!Shooter)
	{
		return nullptr;
	}
	// The pawn's own components hold the first-person view model; the actors attached to it hold Lyra's
	// spawned weapon actor and its SSVisual mesh.
	TArray<AActor*> Owners;
	Shooter->GetAttachedActors(Owners, true, true);
	Owners.Insert(Shooter, 0);
	const bool bLocalView = Shooter->IsLocallyControlled() && Shooter->IsPlayerControlled();
	UStaticMeshComponent* Fallback = nullptr;
	for (AActor* Owner : Owners)
	{
		TInlineComponentArray<UStaticMeshComponent*> Meshes(Owner);
		for (UStaticMeshComponent* Mesh : Meshes)
		{
			if (!Mesh || !Mesh->IsVisible() || FirstSocket(Mesh, Sockets).IsNone())
			{
				continue;
			}
			// The first-person view model is only-owner-see (USSFirstPersonSubsystem).
			if (static_cast<bool>(Mesh->bOnlyOwnerSee) == bLocalView)
			{
				return Mesh;
			}
			Fallback = Fallback ? Fallback : Mesh;
		}
	}
	return Fallback;
}
