// Copyright Southern Spear. All Rights Reserved.

#include "SSObjectivesEditorLibrary.h"

#include "GameFeatureAction_AddComponents.h"
#include "GameFeatureData.h"
#include "Modules/ModuleManager.h"
#include "UObject/UnrealType.h"

IMPLEMENT_MODULE(FDefaultModuleImpl, SouthernSpearObjectivesEditor)

int32 USSObjectivesEditorLibrary::SetGameFeatureComponentGrants(UGameFeatureData* Data, const TArray<FSSComponentGrant>& Grants)
{
	if (!Data)
	{
		UE_LOG(LogTemp, Error, TEXT("SetGameFeatureComponentGrants: no GameFeatureData."));
		return -1;
	}

	TArray<TObjectPtr<UGameFeatureAction>>& Actions = Data->GetMutableActionsInEditor();
	Actions.RemoveAll([](const TObjectPtr<UGameFeatureAction>& Action)
	{
		return Action && Action->IsA<UGameFeatureAction_AddComponents>();
	});

	UGameFeatureAction_AddComponents* Add = NewObject<UGameFeatureAction_AddComponents>(Data, NAME_None, RF_Transactional);
	for (const FSSComponentGrant& Grant : Grants)
	{
		if (!Grant.ActorClass.IsValid() || !Grant.ComponentClass.IsValid())
		{
			UE_LOG(LogTemp, Error, TEXT("SetGameFeatureComponentGrants: empty class path (%s -> %s); refusing."),
				*Grant.ActorClass.ToString(), *Grant.ComponentClass.ToString());
			return -1;
		}
		FGameFeatureComponentEntry& Entry = Add->ComponentList.AddDefaulted_GetRef();
		Entry.ActorClass = TSoftClassPtr<AActor>(Grant.ActorClass);
		Entry.ComponentClass = TSoftClassPtr<UActorComponent>(Grant.ComponentClass);
		Entry.bClientComponent = Grant.bClientComponent;
		Entry.bServerComponent = Grant.bServerComponent;
	}
	Actions.Add(Add);
	Data->MarkPackageDirty();
	return Add->ComponentList.Num();
}

bool USSObjectivesEditorLibrary::SetPropertyFromText(UObject* Target, FName PropertyName, const FString& Value)
{
	FProperty* Property = Target ? Target->GetClass()->FindPropertyByName(PropertyName) : nullptr;
	if (!Property)
	{
		UE_LOG(LogTemp, Error, TEXT("SetPropertyFromText: '%s' has no property '%s'."),
			Target ? *Target->GetName() : TEXT("null"), *PropertyName.ToString());
		return false;
	}
	Target->Modify();
	if (!Property->ImportText_InContainer(*Value, Target, Target, PPF_None))
	{
		UE_LOG(LogTemp, Error, TEXT("SetPropertyFromText: could not parse '%s' for %s.%s."),
			*Value, *Target->GetName(), *PropertyName.ToString());
		return false;
	}
	Target->MarkPackageDirty();
	return true;
}

FString USSObjectivesEditorLibrary::GetPropertyAsText(UObject* Target, FName PropertyName)
{
	FProperty* Property = Target ? Target->GetClass()->FindPropertyByName(PropertyName) : nullptr;
	FString Out;
	if (Property)
	{
		Property->ExportText_InContainer(0, Out, Target, Target, Target, PPF_None);
	}
	return Out;
}

TArray<FString> USSObjectivesEditorLibrary::ListPropertiesAsText(UObject* Target, UClass* StopAtClass)
{
	TArray<FString> Lines;
	if (!Target)
	{
		return Lines;
	}
	for (TFieldIterator<FProperty> It(Target->GetClass(), EFieldIteratorFlags::IncludeSuper); It; ++It)
	{
		const FProperty* Property = *It;
		const UClass* Owner = Property->GetOwnerClass();
		if (StopAtClass && Owner && (Owner == StopAtClass || StopAtClass->IsChildOf(Owner)))
		{
			continue; // declared at or above the stop class
		}
		FString Value;
		Property->ExportText_InContainer(0, Value, Target, Target, Target, PPF_None);
		if (Value.Len() > 300)
		{
			Value = Value.Left(300) + TEXT("...");
		}
		Lines.Add(FString::Printf(TEXT("%s.%s = %s"), Owner ? *Owner->GetName() : TEXT("?"), *Property->GetName(), *Value));
	}
	return Lines;
}
